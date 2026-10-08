# Plan — Versión 5: el segundo motor (MariaDB) y la fábrica

> **Nota (agosto de 2026):** el curso adoptó **SQLAlchemy (solo como ejecutor, con text())** como
> micro-ejecutor en TODOS los repositorios: el SQL sigue escrito a mano
> y parametrizado; cambió el mapeo (`QueryAsync`/`ExecuteAsync` en vez
> del ciclo DataReader) y los SPs se llaman con `DynamicParameters`.
> Las tablas de "calco" entre dialectos siguen valiendo para los
> PROVEEDORES (SQLAlchemy/SqlClient/MySqlConnector) que SQLAlchemy (solo como ejecutor, con text()) usa por debajo.


> Cómo se construye lo especificado en [2_spec.md](2_spec.md). El stack es
> el mismo de siempre (Python/FastAPI, ADO.NET, sin ORM); lo nuevo es el
> cliente **SQLAlchemy** y el patrón **fábrica abstracta**.

---

## 1. Inventario de archivos

**Nuevos (14 de código + 2 de BD):**

```
api_facturas/servicios/ensamblador.py        ← LA FABRICA: un crear_servicio_X por recurso
api_facturas/servicios/fabrica_postgres.py           ← entrega los 11 *Postgres
api_facturas/servicios/fabrica_maria_db.py          ← entrega los 11 *MariaDb
api_facturas/repositorios/Repositorio{Producto,Persona,Factura,Empresa,
    Cliente,Vendedor,Usuario,Rol,Ruta,RolUsuario,RutaRol}maria_db.py   (11)
db/bdfacturas_mariadb.sql                        ← la MISMA BD, dialecto T-SQL
db/init_mariadb.sh                               ← el inicializador (MariaDB no auto-ejecuta)
```

**Crecen (los únicos existentes que se tocan):**

| Archivo | Qué crece |
|---|---|
| `requirements.txt` | ★ paquete **SQLAlchemy** |
| `docker-compose.yml` | ★ servicios `mariadb` (2022, :13335, healthcheck) + `mariadb-init` + variables `Motor` y `ConnectionStrings__MariaDb` en la API |
| `las variables del compose` | ★ cadena `MariaDb` y clave `Motor` (defaults para correr sin Docker) |
| `main.py` | ★ el ensamblador se REESCRIBE alrededor de la fábrica (ver §4) + diagnóstico v5 con `motor` |
| `pruebas/programa.py` | ★ criterio 5: las fábricas eligen sin conectarse |

**Intocables (RNF2):** controllers/, servicios/, models/, models/,
excepciones.py. Ese es el punto de la versión.

## 2. Los 10 repositorios "calcados" (todos menos factura)

La traducción Postgres → MariaDb es **mecánica** — la tabla completa:

| PostgreSQL (v1–v4) | MariaDB (v5) |
|---|---|
| `using SQLAlchemy` | `using SQLAlchemy` |
| `SqlConnection` / `SqlCommand` / `SqlDataReader` | `SQLAlchemyConnection` / `SQLAlchemyCommand` / `SQLAlchemyDataReader` |
| `SqlParameterCollection` | `SQLAlchemyParameterCollection` |
| `SELECT TOP (@limite) …` (al PRINCIPIO) | `SELECT … LIMIT @limite` (al final) |
| Todo lo demás (parámetros `@`, async, `await using`, DBNull del cliente, el SET dinámico del PATCH) | **idéntico** |

BCrypt no se entera del cambio: `RepositorioUsuarioMariaDb` hashea y
verifica EXACTAMENTE igual (el hash es del repositorio, no del motor —
RNF2 de la v3).

## 3. El repositorio de factura MariaDb (el único con diseño propio)

Los SPs de MariaDB devuelven su JSON por un parámetro
`INOUT p_resultado JSON`, y no por un `OUTPUT` como los de PostgreSQL.
Diferencias frente al dialecto que el curso ya conoce:

| Aspecto | PostgreSQL (v2) | MariaDB (v5) |
|---|---|---|
| Invocación | `CommandType.StoredProcedure` | texto `CALL sp_x(…, NULL)` |
| El JSON de salida | parámetro OUTPUT (`SqlDbType.NVarChar, -1`) | el `CALL` devuelve una fila con los `INOUT` |
| El detalle JSON de entrada | `NVARCHAR` que el SP abre con `OPENJSON` | `cast(:productos as json)` |
| Errores de negocio | `THROW` **numerado**: 50003 (consultar: no existe) · 50010 (anular: no existe / ya anulada) | `RAISE EXCEPTION` → SQLSTATE `P0001` + patrón del mensaje |

La traducción de errores — fíjese: MariaDB SÍ numera, así que el
filtro es MÁS preciso que el patrón de texto de PostgreSQL (la lección
de dialectos, en la otra dirección):

```python
catch (MariaDbException e) when ((e.SqlState == 50003 || e.SqlState == 50010)
                             && e.Message.Contains("no existe"))
{
    throw new NoEncontradoExcepcion(e.Message);      // → 404
}
catch (MariaDbException e) when (e.SqlState == 50010 && e.Message.Contains("anulada"))
{
    throw new ConflictoExcepcion(e.Message);         // → 409
}
// Stock insuficiente (trigger), mínimo de renglones, FK → suben → 500.
```

## 4. El ensamblador con fábrica (main.py)

La lista de la v3 ("este dolor es el argumento del segundo motor") se
cura así:

```python
// UN punto del código decide el motor (default: postgres, el de siempre):
var motor = builder.Configuration["Motor"] ?? "postgres";
el ensamblador fabrica = motor switch
{
    "postgres"  => new FabricaPostgres(cadenaPostgres),
    "mariadb" => new FabricaMariaDb(cadenaMariaDb),
    _ => throw new InvalidOperationException(
             $"Motor desconocido: '{motor}' (use postgres o mariadb)."),
};

// Las 11 rebanadas, ahora CIEGAS al motor:
el ensamblador<IRepositorioProducto>(_ => fabrica.CrearRepositorioProducto());
el ensamblador<IServicioProducto, ServicioProducto>();
// … (mismo par para las otras 10 rebanadas)
```

La cuenta didáctica: agregar MariaDB al anexo costará **una clase**
(`FabricaMariaDb`) **y un case** — no 11 registros nuevos. Eso compra la
fábrica.

## 5. El compose con dos motores (y la lección del inicializador)

- Servicio `mariadb` (2022): healthcheck REAL con psql y
  `start_period: 30s` (el motor tarda). Pide ~2 GB de RAM — el contraste
  de pesos con PostgreSQL alpine (~50 MB) también es contenido.
- **`mariadb-init`**: la v1 lo prometió — "cuando llegue un motor que
  NO se siembre solo, se entenderá el patrón inicializador". Aquí está:
  un contenedor que espera el healthcheck, corre
  `db/bdfacturas_mariadb.sql` UNA vez (idempotente) y muere. La API
  suma `depends_on: service_completed_successfully`.
- Puerto publicado **13335** (curso; la reconstrucción del estudiante
  usa 15562).
- El interruptor: `Motor: ${DB_PROVIDER:-postgres}` —
  `DB_PROVIDER=mariadb docker compose up -d api-facturas` recrea SOLO la
  API apuntando al motor nuevo (los DOS motores siempre están arriba).

## 6. La prueba de capas crece (criterio 5)

Las fábricas se prueban SIN base de datos: construir un repositorio no
abre conexiones. El proyecto `pruebas/` verifica que cada fábrica entrega
instancias del dialecto correcto (`is RepositorioProductoMariaDb`,
etc.) con cadenas de conexión de mentira.

## 7. Chequeo de constitución

> **La compuerta 2** del método (ver [SDD_SPECKIT](../../../conceptos/SDD_SPECKIT.md)):
> antes de pasar a `8_tasks.md` se revisa la
> [constitución](../../1_constitution.md) **artículo por artículo**. Si algo
> no cumple, o se corrige el plan, o se enmienda la constitución. Nunca se
> deja pasar "por esta vez".

| Artículo | Cómo lo cumple esta versión |
|---|---|
| **1** — El curso es POR VERSIONES y la especificación manda | El alcance de esta versión es el que declara [2_spec.md](2_spec.md) §2, y **no anticipa** nada de las siguientes. Cierra con commit y tag. |
| **2** — Stack: Python y FastAPI, con el SQL a la vista | Python sobre FastAPI, SQL escrito a mano y **siempre parametrizado**, sin ORM de entidades. Los paquetes son los que el artículo permite (§1 de este plan). |
| **3** — Arquitectura en capas con interfaces, desde el día 1 | Controlador → interfaz de servicio → interfaz de repositorio → repositorio (§3 de este plan). Solo el ensamblador conoce clases concretas. |
| **4** — Un solo comando | `docker compose up -d --build` deja la versión funcionando (§5 de este plan). |
| **5** — La base de datos viene DADA | La BD `bdfacturas` viene dada por los scripts de `db/`; esta versión solo nombra las tablas que su alcance le permite ([5_data_model.md](5_data_model.md)). |
| **6** — Todo en español, comentado para principiantes | Nombres, rutas y mensajes en español, con comentarios línea a línea en el código. |
| **7** — Contratos exactos | [6_contracts.md](6_contracts.md) fija verbos, rutas, códigos y formatos exactos, incluidos los desenlaces de error. |
| **8** — Convenciones fijas | Puertos, rutas, sobre de respuesta y catálogo de errores, tal como los fija el artículo. |

**Complejidad justificada:** si esta versión se desvía de algún artículo,
la desviación va aquí, con la alternativa más simple que se descartó y por
qué no sirvió. Sin desviaciones anotadas, se entiende que no las hay.
