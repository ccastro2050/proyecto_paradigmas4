# Plan técnico — Versión 1: las seis tablas sin FK (Python/FastAPI + Flask)

> **Versión 1** · CÓMO construir lo especificado en [2_spec.md](2_spec.md).
> El porqué de cada decisión: [4_research.md](4_research.md) · contratos
> exactos: [6_contracts.md](6_contracts.md) · orden: [8_tasks.md](8_tasks.md).

---

## 1. Stack

| Pieza | Elección | Por qué |
|---|---|---|
| Lenguaje / framework | **Python sobre FastAPI (.NET 10)** | El stack del curso; controladores con atributos, DI integrada, async nativo |
| Acceso a datos | **SQLAlchemy (solo como ejecutor, con text())** sobre `SQLAlchemy`, con SQL parametrizado a mano | SQL visible — SQLAlchemy (solo como ejecutor, con text()) mapea fila→objeto pero NO genera SQL (Art. 2, D1) |
| Validación | **Una petición por verbo** con anotaciones (`[Required]`, `[Range]`…) | El framework valida el body contra la petición y responde 422 — la petición ES la frontera |
| Motor (v1) | **PostgreSQL 2022** (contenedor oficial) | El motor natural del ecosistema .NET; los otros llegan en v3/v4 |
| Contenedor de la API | `python:3.12-slim` + `uvicorn --reload` | Guardar un `.py` recompila y reinicia solo (ciclo de desarrollo del curso) |

## 2. Estructura de carpetas

```
(raíz del proyecto)
├── docker-compose.yml                # UN comando: mariadb + api (crece por versiones)
├── db/
│   └── init.sql       # la BD completa, PROVISTA (se copia, no se genera)
└── api_facturas/
    ├── requirements.txt            # el proyecto .NET (paquetes: SQLAlchemy y Swashbuckle)
    ├── main.py                    # punto de entrada: ENSAMBLADOR (DI) + 422 + rutas
    ├── las variables del compose              # cadena de conexión (default localhost,11463)
    ├── Dockerfile                    # sdk:10.0 + uvicorn --reload (puerto 8005)
    ├── models/
    │   └── producto.py               # el MODELO = la ENTIDAD: 4 propiedades tipadas
    ├── models/
    │   ├── producto_crear.py          # petición del POST (todo obligatorio)
    │   ├── producto_reemplazo.py      # petición del PUT (todo obligatorio, sin código)
    │   └── producto_actualizar.py     # petición del PATCH (todo opcional)
    ├── controllers/
    │   └── producto_controller.py     # HTTP: atributos de verbo, try/catch → códigos
    ├── servicios/
    │   ├── i_servicio_producto.py      # interface del servicio
    │   └── servicio_producto.py       # reglas de negocio; recibe IRepositorioProducto
    ├── repositorios/
    │   ├── i_repositorio_producto.py   # interface: 5 métodos de datos (async)
    │   └── repositorio_producto_postgresql.py   # SQLAlchemy (solo como ejecutor, con text()) + SQL a mano parametrizado
    ├── excepciones.py
    │   └── no_encontrado_excepcion.py  # la excepción de negocio que el controller vuelve 404
    └── pruebas/
        ├── PruebaCapasrequirements.txt        # proyecto de consola aparte (criterio 6)
        └── programa.py               # el servicio con un repositorio falso, sin BD
```

### 2bis. El front, que es un proyecto APARTE

```
front_flask/
├── requirements.txt          sin UN SOLO paquete de datos
├── main.py                    registra ServicioProducto con su HttpClient
├── Dockerfile                    SDK + uvicorn --reload, igual que la API
├── las variables del compose              UrlApi (el compose la sobreescribe)
├── models/
│   └── producto.py               la clase DEL FRONT, no la de la API
├── servicios/
│   └── servicio_producto.py       el ÚNICO sitio que sabe de HTTP
├── Components/
│   ├── App.html · Routes.html · _Imports.html
│   ├── Layout/   MainLayout · NavMenu
│   └── Pages/    Home · Productos
└── wwwroot/
    ├── lib/bootstrap/            SERVIDO DESDE AQUI, nunca por CDN
    └── app.css                   la capa del proyecto, ENCIMA de Bootstrap
```

**Que el front y la API estén los dos en Python no cambia nada**, y hay que
cuidarlo: la tentación de compartir una clase existe aquí y no existiría con
dos lenguajes distintos.

| Regla | Por qué |
|---|---|
| **El front tiene SU propia clase `Producto`** | Se parece a la de la API porque el **contrato** es el mismo, no porque sea la misma. Una referencia de proyecto ataría los dos procesos |
| **`requirements.txt` no tiene SQLAlchemy** | No es un olvido: es la comprobación de que este proceso **no puede** llegar a PostgreSQL ni queriendo |
| **Un servicio POR RECURSO** | Hoy `ServicioProducto`. Con doce recursos, doce servicios — no un `ApiService` con la tabla como parámetro |
| **Bootstrap SI, por CDN NO** | Se sirve desde `wwwroot/lib/bootstrap/`, y `wwwroot/app.css` va **encima** con las clases del dominio (`.tarjeta`, `.campos`, `.acciones`). A igual especificidad gana el ultimo que carga: por eso el orden no es decorativo |

## 3. Arquitectura en capas (flujo de una petición)

```
HTTP → FastAPI routing        (los decoradores @router.get/@router.post deciden el método)
     → validación del MODELO   (los Field() del modelo del verbo → 422 automático)
     → producto_controller     (try/except: traduce excepciones a códigos HTTP)
     → IServicioProducto       (Protocol — reglas de negocio)
     → IRepositorioProducto    (Protocol — el servicio no sabe qué motor hay detrás)
     → RepositorioProductoPostgreSQL (SQLAlchemy como ejecutor, con text() y :param)
     → PostgreSQL
```

**Regla de dependencias:** controller → servicio → interfaz de repositorio.
Solo el ENSAMBLADOR (la sección de DI de `main.py`) conoce clases
concretas.

## 4. Decisiones de diseño clave

### 4.1 Interfaces de Python desde v1
```python
from typing import Protocol


class IRepositorioProducto(Protocol):
    async def obtener_todos(self, limite: int) -> list[dict]: ...
    async def obtener_por_codigo(self, codigo: str) -> dict | None: ...
    async def crear(self, datos: dict) -> bool: ...
    async def actualizar(self, codigo: str, datos: dict) -> int: ...
    async def eliminar(self, codigo: str) -> int: ...
```

El servicio recibe **el contrato** por el constructor (lo inyecta el
ensamblador). Esto es lo que compra la **v5**: otro motor será otra clase con
los mismos cinco métodos.

> **Y aquí hay una diferencia con el gemelo .NET que conviene ver:** una clase
> de Python cumple un `Protocol` **sin heredar de nada**. Basta con tener los
> métodos —tipado estructural, PEP 544—. En C# hay que escribir
> `: IRepositorioProducto` o no compila.
>
> Las dos formas tienen su precio: allá el compilador avisa si falta un
> método; aquí se descubre al llamarlo. Lo que no cambia es la **decisión**:
> el servicio depende de la abstracción.

> **`actualizar` recibe un diccionario** y las demás también, porque un PATCH
> puede traer solo algunos campos y el repositorio arma el `SET` con lo que
> llegó. Los **nombres** de esas claves salen de los modelos Pydantic, no del
> cliente: por eso es seguro interpolarlos en el SQL, y los **valores** van
> parametrizados.

### 4.2 La validación vive en las PETICIONES (una por verbo)
FastAPI valida el body contra la petición del verbo ANTES de ejecutar el
método del controlador — el 422 sale solo (personalizado en `main.py`
para responder `{estado, mensaje, errores:[…]}`):

- `ProductoCrear`      → POST: todos obligatorios (con código)
- `ProductoReemplazo`  → PUT: todos obligatorios (el código va en la URL)
- `ProductoActualizar` → PATCH: todos opcionales (se valida lo que llegue)

Reglas: `codigo` 1–10 caracteres · `nombre` no vacío · `stock` entero ≥ 0 ·
`valorunitario` numérico ≥ 0. **El tipo también es regla**: `stock` es
`int?` — un `7.5` o un `"texto"` no encajan y caen en 422. (El body vacío
en PATCH es 400 y lo decide el **servicio**: no es un problema de forma
sino de regla de negocio.)

### 4.3 El ensamblador: la sección de DI de main.py
```python
el ensamblador<IRepositorioProducto>(
    _ => new RepositorioProductoPostgres(cadenaConexion));
el ensamblador<IServicioProducto, ServicioProducto>();
```
Sin fábrica multi-motor ni selección: v1 tiene UN motor y el código lo dice.
Cuando v3 agregue PostgreSQL, **solo esta sección** se convierte en la
fábrica real — controllers y servicios no se tocan (ese es el examen de la
v3).

### 4.4 SQL del repositorio (SQLAlchemy (solo como ejecutor, con text()), siempre parametrizado)
```sql
SELECT codigo, nombre, stock, valorunitario FROM producto ORDER BY codigo LIMIT @limite
SELECT … WHERE codigo = @codigo
INSERT INTO producto (codigo, nombre, stock, valorunitario) VALUES (@codigo, @nombre, @stock, @valorunitario)
UPDATE producto SET … WHERE codigo = @codigo_clave   -- los campos que lleguen (PUT: los 3; PATCH: los enviados)
DELETE FROM producto WHERE codigo = @codigo
```
- `LIMIT @limite` es el Top-N del dialecto PostgreSQL (va al FINAL y
  acepta parámetro).
- SQLAlchemy (solo como ejecutor, con text()) ejecuta ese SQL tal cual: `QueryAsync<Producto>` para lecturas
  (mapea columna→propiedad por nombre) y `ExecuteAsync` para escrituras
  (devuelve filas afectadas). Conexión por operación con `await using`;
  todo `async`.
- El SET del UPDATE se arma solo con columnas que salen de las PETICIONES
  (lista blanca), nunca con claves del cliente.
- Detalle amable del motor: en PostgreSQL, las filas afectadas de un UPDATE
  cuentan las que CUMPLIERON el WHERE (aunque el valor nuevo sea igual al
  viejo) — un PATCH con el mismo valor reporta 1 fila, sin trucos.

### 4.5 Traducción de excepciones a HTTP (en el controller)
| Situación | HTTP |
|---|---|
| (Body con errores de forma — lo responde el framework con la lista) | 422 |
| `ArgumentException` (regla de negocio: límite ≤ 0, body vacío en PATCH) | 400 |
| `NoEncontradoExcepcion` (código inexistente) | 404 |
| `SQLAlchemyException` y cualquier otra | 500 (mensaje del motor en `detalle`) |

Cada método del controller lleva su propio `try/catch` plano, de arriba a
abajo — sin indirecciones.

### 4.6 PostgreSQL se siembra SOLO (sin inicializador)
PostgreSQL ejecuta automáticamente los scripts montados en
`/docker-entrypoint-initdb.d/` la PRIMERA vez (cuando su volumen está
vacío): el compose monta `db/init.sql` ahí y no necesita
ningún contenedor extra. La API arranca con `depends_on: condition:
service_healthy` — cuando la BD ya RESPONDE (y por tanto ya se sembró).
(Otros motores, como PostgreSQL, NO tienen este mecanismo y exigen un
contenedor inicializador: esa lección llegará con el segundo motor.)

## 5. Docker: un solo comando desde v1

La constitución (Artículo 4) manda: `docker compose up -d --build` deja TODO
funcionando. En v1 eso son **dos servicios**: `mariadb` (11463 al host,
se siembra solo) y `api-facturas` (8005, código montado +
`uvicorn --reload`, `bin/` y `obj/` en volúmenes anónimos para no mezclar
compilados de Linux con los de Windows). El detalle línea por línea está en
el `docker-compose.yml` de la raíz, comentado.

## 6. Chequeo de constitución

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
