# Plan — Versión 2: más tablas (los moldes y la factura)

> Cómo se construye lo especificado en [2_spec.md](2_spec.md). El stack no
> cambia (FastAPI + SQLAlchemy async con text() + asyncpg + Pydantic):
> cambia la ESCALA — el molde de la v1 en serie, y la primera entidad que
> habla con procedimientos almacenados.

---

## 1. Inventario de archivos

**Nuevos (26):**

```
api_facturas/excepciones.py                      ← ConflictoError (→ 409)
api_facturas/models/{persona,empresa,cliente,vendedor,factura}.py        (5)
api_facturas/repositorios/abstracciones/i_repositorio_{persona,empresa,cliente,vendedor,factura}.py   (5)
api_facturas/repositorios/repositorio_{persona,empresa,cliente,vendedor,factura}_postgresql.py        (5)
api_facturas/servicios/abstracciones/i_servicio_{persona,empresa,cliente,vendedor,factura}.py         (5)
api_facturas/servicios/servicio_{persona,empresa,cliente,vendedor}.py + servicio_factura.py           (5)
api_facturas/controllers/{persona,empresa,cliente,vendedor,factura}_controller.py                     (5)
```

**Crecen (los únicos existentes que se tocan):**

| Archivo | Qué crece |
|---|---|
| `main.py` | ★ 5 `include_router` nuevos + `version="v2"` |
| `servicios/ensamblador.py` | ★ 5 funciones `crear_servicio_x()` (SIGUE siendo funciones simples — la fábrica es de la v3) |
| `pruebas/prueba_capas.py` | ★ persona con repositorio falso (criterio 6) |

**Intocables:** todo lo de producto y `db/init.sql` (las tablas, SPs y
trigger están ahí desde la v1 — infraestructura dada).

## 2. Los cuatro moldes (el calco por entidad)

La rebanada de producto se replica cambiando SOLO nombres, PK y campos:

| Pieza | producto (v1) | persona | empresa | cliente | vendedor |
|---|---|---|---|---|---|
| PK | codigo str | codigo str | codigo str | **id SERIAL** | **id SERIAL** |
| Ruta de detalle | `/{codigo}` | `/{codigo}` | `/{codigo}` | `/{id_cliente}` (int) | `/{id_vendedor}` (int) |
| Métodos repo | obtener_por_codigo | igual | igual | **obtener_por_id** | **obtener_por_id** |
| Particular | — | — | — | credito/fkcodempresa OPCIONALES al crear (D6) | — |

Reglas del calco:
- El **INSERT de cliente es dinámico**: solo las columnas enviadas — si el
  cliente no manda `credito`, el DEFAULT 0 lo pone la BD; si no manda
  `fkcodempresa`, queda NULL. (El mismo truco del SET dinámico del PATCH.)
- El PUT de cliente escribe las 3 columnas (con `fkcodempresa = NULL` si
  llegó null: reemplazo completo es reemplazo completo).
- Las entidades con PK SERIAL no la reciben en el POST: la asigna la BD.

## 3. El repositorio de factura (el único con diseño propio)

Los SPs de `db/init.sql` son `PROCEDURE` con `INOUT p_resultado JSON`. En
PostgreSQL el `CALL` devuelve los INOUT como UNA FILA de resultado:

```python
sql = text("CALL sp_insertar_factura_y_productosporfactura("
           ":cliente, :vendedor, cast(:productos as json), 1, NULL)")
async with self._obtener_engine().begin() as conexion:   # transacción
    resultado = await conexion.execute(sql, parametros)
    fila = resultado.first()          # la fila de los INOUT
    return json.loads(fila[0])        # p_resultado: JSON → dict
```

Los 4 métodos usan el mismo ayudante: `sp_listar…(NULL)`,
`sp_consultar…(:numero, NULL)`, `sp_insertar…(…)`, `sp_anular_factura(:numero, NULL)`.

**La traducción de errores** (los `RAISE EXCEPTION` de los SPs llegan como
`DBAPIError` con SQLSTATE `P0001`):

| El SP dice | La API traduce | HTTP |
|---|---|---|
| `Factura N no existe` | `LookupError` | 404 |
| `Factura N ya está anulada` | `ConflictoError` (nueva, `excepciones.py`) | 409 |
| `Stock insuficiente…` (trigger) · FK · lo demás | sube tal cual | 500 |

El patrón se decide por SQLSTATE + texto del mensaje — y NADIE por encima
del repositorio conoce `DBAPIError`.

## 4. Modelos de factura (la frontera valida la LISTA)

```python
class RenglonFactura(BaseModel):
    codigo: str = Field(min_length=1, max_length=20)
    cantidad: int = Field(ge=1)

class FacturaCrear(BaseModel):
    fkidcliente: int = Field(ge=1)
    fkidvendedor: int = Field(ge=1)
    productos: list[RenglonFactura] = Field(min_length=1)   # [] → 422
```

Nadie envía subtotales: el modelo no tiene dónde ponerlos — la frontera
también ES contrato.

## 5. El ensamblador crece (y todavía no duele lo suficiente)

Cinco funciones nuevas idénticas a `crear_servicio_producto()`. La lista
empieza a oler a repetición — ese olor es el argumento de la fábrica, pero
la fábrica SIN un segundo motor sería especulación (YAGNI): llega en la v3
con MariaDB, cuando algo la justifique.

## 6. Chequeo de constitución

> **La compuerta 2** del método (ver [SDD_SPECKIT](../../../SDD_SPECKIT.md)):
> antes de pasar a `8_tasks.md` se revisa la
> [constitución](../../1_constitution.md) **artículo por artículo**. Si algo
> no cumple, o se corrige el plan, o se enmienda la constitución. Nunca se
> deja pasar "por esta vez".

| Artículo | Cómo lo cumple esta versión |
|---|---|
| **1** — Propósito didáctico ante todo | Todo en español y comentado para principiantes; se prefiere lo explícito y legible sobre lo compacto. |
| **2** — Arquitectura de 3 capas estricta | Las capas que esta versión construye respetan la separación estricta (§3 de este plan): el front no toca la BD y la API no devuelve HTML. |
| **3** — Independencia del motor de base de datos | El acceso a datos pasa por interfaces. Si esta versión trae un solo motor, la independencia todavía es **meta**, no estado — así lo dice la propia constitución en su encabezado. |
| **4** — Un solo comando para arrancar | `docker compose up -d --build` deja funcionando lo que esta versión declara (§5 de este plan); lo que aún no existe no se exige. |
| **5** — Persistencia y reproducibilidad | Los datos viven en volúmenes; `docker compose down -v` devuelve la BD a su estado original. |
| **6** — Convenciones fijas | Puertos, rutas y convenciones de nombres, tal como los fija el artículo. |
| **7** — Desarrollo con recarga en caliente | El código va montado en el contenedor: guardar un archivo recarga sin reconstruir la imagen. |
| **8** — Seguridad en su justa medida académica | Credenciales didácticas y sin secretos reales; la seguridad se mantiene en la medida que el artículo define. |

**Complejidad justificada:** si esta versión se desvía de algún artículo,
la desviación va aquí, con la alternativa más simple que se descartó y por
qué no sirvió. Sin desviaciones anotadas, se entiende que no las hay.
