# Plan — Versión 3: el segundo motor (MariaDB) y la fábrica

> Cómo se construye lo especificado en [2_spec.md](2_spec.md). El stack no
> cambia (FastAPI + SQLAlchemy async con text() + Pydantic); lo nuevo es
> el driver **aiomysql** y que el ensamblador se convierte en **fábrica**.

---

## 1. Inventario de archivos

**Nuevos (7):**

```
db/init_mariadb.sql                                  ← la MISMA bdfacturas, dialecto MariaDB
api_facturas/repositorios/repositorio_{producto,persona,empresa,cliente,
    vendedor,factura}_mariadb.py                     ← los 6 dialectos MariaDB
```

**Crecen (los únicos existentes que se tocan):**

| Archivo | Qué crece |
|---|---|
| `docker-compose.yml` | ★ servicio `mariadb` (11, puerto 13335, se inicializa solo) + `DB_MARIADB` y `DB_PROVIDER: ${DB_PROVIDER:-postgres}` en la API |
| `api_facturas/requirements.txt` | ★ **aiomysql** (el driver async de MySQL/MariaDB) |
| `servicios/ensamblador.py` | ★ se REESCRIBE como la fábrica real (ver §3) |
| `main.py` | ★ `version="v3"` + `motor` en el diagnóstico |
| `pruebas/prueba_capas.py` | ★ criterio 5: la fábrica elige sin conectarse |

**Intocables (RNF2):** `controllers/`, `servicios/servicio_*.py`,
`servicios/abstracciones/`, `models/`, `excepciones.py` y todo lo de
producto/persona/empresa/cliente/vendedor/factura por encima de la capa
de datos. Ese es el punto de la versión.

## 2. Los 5 repositorios "calcados" (todos menos factura)

La traducción PostgreSQL → MariaDB de los moldes es **casi nula** — esa
es la sorpresa didáctica:

| Aspecto | PostgreSQL (v1/v2) | MariaDB (v3) |
|---|---|---|
| Clase | `RepositorioXPostgreSQL` | `RepositorioXMariaDB` |
| Cadena | `postgresql+asyncpg://…` | `mysql+aiomysql://…` |
| El SQL de los moldes (SELECT/INSERT/UPDATE/DELETE, `LIMIT :limite`, SET dinámico) | **idéntico** | **idéntico** |

SQLAlchemy con `text()` y parámetros `:nombre` absorbe el dialecto: el
SQL estándar de los moldes corre igual en ambos motores. (El INSERT
dinámico de cliente también — los DEFAULT los sigue poniendo la BD.)

## 3. La fábrica (ensamblador.py se reescribe)

La promesa de la v1 ("cuando la v3 agregue MariaDB, SOLO este archivo se
convertirá en la fábrica real") se paga así:

```python
_FABRICAS = {
    "postgres": {
        "variable_cadena": "DB_POSTGRES",
        "repositorios": {
            "producto": RepositorioProductoPostgreSQL,
            # … las 6 entidades
        },
    },
    "mariadb": {
        "variable_cadena": "DB_MARIADB",
        "repositorios": {
            "producto": RepositorioProductoMariaDB,
            # … las 6 entidades
        },
    },
}

def _crear_repositorio(entidad: str):
    proveedor = os.environ.get("DB_PROVIDER", "postgres")
    if proveedor not in _FABRICAS:
        raise ValueError(f"DB_PROVIDER inválido: '{proveedor}' "
                         f"(use {', '.join(_FABRICAS)})")
    fabrica = _FABRICAS[proveedor]
    clase = fabrica["repositorios"][entidad]
    return clase(os.environ[fabrica["variable_cadena"]])
```

Las funciones `crear_servicio_x()` conservan su firma (los controllers no
se tocan) y por dentro piden el repositorio a la fábrica. La cuenta
didáctica: **agregar SQL Server en la v4 = un bloque más en `_FABRICAS`**
— ni un `if` regado por el código.

## 4. El repositorio de factura MariaDB (el único con diseño propio)

Los SPs de MariaDB devuelven su JSON por un parámetro **OUT** (no hay
INOUT-como-fila): el CALL se hace en dos pasos sobre LA MISMA conexión:

```python
async with self._obtener_engine().begin() as conexion:
    await conexion.execute(text(
        "CALL sp_insertar_factura_y_productosporfactura("
        ":cliente, :vendedor, :productos, 1, @salida)"), parametros)
    fila = (await conexion.execute(text("SELECT @salida"))).first()
    # @salida es LONGTEXT → json.loads
```

(El JSON de entrada viaja como texto plano: en MariaDB `JSON` ES
`LONGTEXT` — no hay cast.)

**La traducción de errores:** los `SIGNAL SQLSTATE '45000'` de los SPs y
triggers llegan como `DBAPIError` con **código 1644**
(ER_SIGNAL_EXCEPTION). El patrón del mensaje decide — mismos textos que
en PostgreSQL:

| El SP dice | La API traduce | HTTP |
|---|---|---|
| `Factura N no existe` | `LookupError` | 404 |
| `Factura N ya está anulada` | `ConflictoError` | 409 |
| `Stock insuficiente…` (trigger) · FK · resto | sube tal cual | 500 |

## 5. El compose con dos motores

- `mariadb:11` también ejecuta los scripts de `/docker-entrypoint-initdb.d/`
  la primera vez — igual que PostgreSQL, sin contenedor inicializador.
- Puerto publicado **13335** (libre en el mapa del curso; la
  reconstrucción del estudiante usa 13435).
- El interruptor vive en el compose: `DB_PROVIDER: ${DB_PROVIDER:-postgres}`.
  Ambos motores SIEMPRE arriba; lo que cambia es a cuál le habla la API.

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
