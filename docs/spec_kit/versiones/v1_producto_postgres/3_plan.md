# Plan técnico — API Facturas **v1**: producto + PostgreSQL

> **Versión 1** · CÓMO construir lo especificado en [2_spec.md](2_spec.md).
> Contratos exactos: [6_contracts.md](6_contracts.md) · orden: [8_tasks.md](8_tasks.md).

---

## 1. Stack (el mismo de la visión final, recortado a lo que v1 usa)

| Pieza | Elección | Por qué |
|---|---|---|
| Lenguaje | Python 3.12 | Estándar del proyecto |
| Framework web | FastAPI | Async nativo, Swagger automático, integra Pydantic |
| Validación | Pydantic v2 | El modelo `Producto` ES la validación de entrada |
| Acceso a datos | SQLAlchemy 2 async, `text()` + parámetros | SQL visible; un solo estilo para los motores futuros |
| Driver | asyncpg | Async puro para PostgreSQL |
| Servidor | uvicorn | Servidor ASGI estándar |
| Configuración | variable de entorno `DB_POSTGRES` | Suficiente para un motor; pydantic-settings llega cuando haya más variables |

## 2. Estructura de carpetas (subconjunto exacto de la final)

```
(raíz del proyecto)
├── docker-compose.yml                # UN comando: postgres + api-facturas (crece por versiones)
├── db/
│   └── init.sql                      # la BD completa, PROVISTA (se copia, no se genera)
└── api_facturas/
    ├── Dockerfile                    # python:3.12-slim + requirements (el compose lo construye)
    ├── requirements.txt
    ├── main.py                       # crea FastAPI, registra router, endpoint /
    ├── models/
    │   └── producto.py               # Pydantic: Producto, ProductoReemplazo y ProductoActualizar
    ├── controllers/
    │   └── producto_controller.py    # los 6 endpoints de producto (router prefix="/api")
    ├── servicios/
    │   ├── abstracciones/
    │   │   └── i_servicio_producto.py    # Protocol del servicio
    │   ├── servicio_producto.py          # reglas de negocio; recibe IRepositorioProducto
    │   └── ensamblador.py                # crear_servicio_producto() — proto-fábrica (ver §4.3)
    └── repositorios/
        ├── abstracciones/
        │   └── i_repositorio_producto.py # Protocol: 5 métodos async
        └── repositorio_producto_postgresql.py
```

Las carpetas y nombres coinciden con la visión final: cuando v2 agregue
`persona.py` o v3 agregue `repositorio_producto_mysql_mariadb.py`, **caen en su
sitio sin mover nada**.

## 3. Arquitectura en capas (flujo de una petición)

```
HTTP → producto_controller  (valida forma con Pydantic; traduce excepciones a códigos)
     → ServicioProducto     (reglas: código no vacío, normalización)
     → IRepositorioProducto (interfaz — el servicio no sabe qué motor hay detrás)
     → RepositorioProductoPostgreSQL (SQL parametrizado, engine async)
     → PostgreSQL
```

**Regla de dependencias:** controller → servicio → interfaz de repositorio.
Solo `ensamblador.py` conoce la clase concreta.

## 4. Decisiones de diseño clave

### 4.1 Interfaces con `typing.Protocol` desde v1
`IRepositorioProducto` define los 5 métodos async:
`obtener_todos(limite)`, `obtener_por_codigo`, `crear`, `actualizar` (lo usan
PUT y PATCH — recibe el dict de campos a escribir) y `eliminar`.
El servicio recibe **la interfaz** por constructor. Esto es lo que compra la
v3: un segundo motor será solo otra clase que cumpla el mismo Protocol.

### 4.2 Pydantic como frontera de entrada (un modelo por semántica HTTP)
```python
class Producto(BaseModel):             # POST: el recurso completo, con su código
    codigo: str = Field(min_length=1, max_length=20)
    nombre: str = Field(min_length=1)
    stock: int = Field(ge=0)
    valorunitario: Decimal = Field(ge=0)

class ProductoReemplazo(BaseModel):    # PUT: reemplazo completo (el código va en la URL)
    nombre: str = Field(min_length=1)
    stock: int = Field(ge=0)
    valorunitario: Decimal = Field(ge=0)

class ProductoActualizar(BaseModel):   # PATCH: parcial, todos opcionales
    nombre: str | None = Field(default=None, min_length=1)
    stock: int | None = Field(default=None, ge=0)
    valorunitario: Decimal | None = Field(default=None, ge=0)
```
Un body inválido muere en 422 **antes** de tocar servicio o BD. Los tres
modelos materializan la semántica de cada verbo: POST trae todo, PUT exige
todo, PATCH acepta cualquier subconjunto (pero no vacío — eso lo valida el
servicio con 400).

### 4.3 `ensamblador.py`: la proto-fábrica honesta
```python
def crear_servicio_producto() -> IServicioProducto:
    repositorio = RepositorioProductoPostgreSQL(os.environ["DB_POSTGRES"])
    return ServicioProducto(repositorio)
```
Tres líneas, sin diccionarios ni `DB_PROVIDER`: v1 tiene UN motor y el código
lo dice. Cuando v3 agregue MariaDB, **solo este archivo** se convierte en la
fábrica real — controllers y servicios no se tocan (ese es el examen de la v3).

### 4.4 SQL del repositorio
`text()` + parámetros nombrados, identificadores fijos (la entidad es conocida
— cada entidad tiene su propia ruta y su propio contrato):

```sql
SELECT codigo, nombre, stock, valorunitario FROM producto ORDER BY codigo LIMIT :limite
SELECT … WHERE codigo = :codigo
INSERT INTO producto (codigo, nombre, stock, valorunitario) VALUES (:codigo, :nombre, :stock, :valorunitario)
UPDATE producto SET … WHERE codigo = :codigo      -- los campos que lleguen (PUT: los 3; PATCH: los enviados)
DELETE FROM producto WHERE codigo = :codigo
```
Engine async creado perezosamente y reutilizado por instancia.
`Decimal` → float al serializar.

### 4.5 Traducción de excepciones (en el controller)
| Excepción | HTTP |
|---|---|
| `ValueError` (validación del servicio) | 400 |
| `LookupError` (no existe el código) | 404 |
| cualquier otra (error del motor) | 500 con el mensaje en `detalle` |

(El 422 lo produce FastAPI/Pydantic solo, antes del controller.)

### 4.6 FastAPI
```python
app = FastAPI(title="API Facturas", version="v1")   # /docs y /redoc por defecto
app.include_router(router_producto, prefix="/api", tags=["Producto"])
```

## 5. Docker: un solo comando desde v1

La constitución (Artículo 4) manda: `docker compose up -d --build` deja TODO
funcionando. En v1 eso son **dos servicios**:

```yaml
services:
  postgres:            # postgres:16-alpine + db/init.sql (la BD completa)
    # volumen pgdata (persistencia) · puerto 15435 al host · healthcheck pg_isready
  api-facturas:        # build: ./api_facturas (su Dockerfile)
    # código montado como volumen + uvicorn --reload → guardar recarga solo
    # DB_POSTGRES apunta al host interno "postgres:5432" (nombre del servicio)
    # depends_on: postgres con condition: service_healthy
volumes:
  pgdata:
```

`api_facturas/Dockerfile`: `python:3.12-slim` → copiar `requirements.txt` +
`pip install` (capa cacheada) → copiar el código → `CMD uvicorn`.

**Durante la construcción fase a fase** también se puede correr la API local
(venv + `uvicorn --reload` con `DB_POSTGRES` hacia `localhost:15435`) — es la
misma API; el compose es la forma oficial de entrega.

## 6. Convenciones

Las de la constitución: todo en español, docstring de apertura por archivo,
snake_case en archivos/funciones, PascalCase en clases, prefijo `i_`/`I` en
interfaces, comentarios didácticos.
