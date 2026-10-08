# La arquitectura de este software

> **Qué es este documento.** Qué piezas hay, quién habla con quién, y la
> pregunta que sale sola al ver un repositorio: **¿esto es un monolito?**
>
> Todo lo que dice está medido en este repositorio. Donde hay un número, se
> puede contar.
>
> Versión 1.0 · 7 de octubre de 2026.

---

## 1. Cinco procesos, y dos son nuestros

Levantar el sistema enciende **cinco contenedores**:

| Contenedor | Qué es | Puerto |
|---|---|---|
| **`front-flask`** | Python + **Flask** (Jinja2). El único que le habla a la persona | **8046** |
| **`api-facturas`** | Python + **FastAPI**. El único que habla con la base de datos | **8005** |
| **`postgres`** | PostgreSQL — **el motor de las cuatro versiones del curso** | 15435 |
| **`mariadb`** | El segundo motor. **Adelanto de la v5** | 13335 |
| **`sqlserver`** | El tercero. **Adelanto de la v5** | 11435 |

```
  Navegador ──HTTP──▶ front-flask ──HTTP──▶ api-facturas ──SQL──▶ postgres
   (persona)            :8046                  :8005              :15435
```

> **De los cinco, solo dos son código nuestro:** el front y la API. Los tres
> motores son software de terceros que se configura, no que se escribe.
>
> **Y la regla que sostiene el diseño:** el front **nunca** toca la base de
> datos. Se comprueba en un minuto — busque `sqlalchemy`, `psycopg` o una
> cadena de conexión dentro de `front_flask/`: no hay ninguna, y no puede
> haberla.

---

## 2. ¿Esto es un monolito?

La respuesta corta: **la API es un monolito, el front también, y el sistema
no.**

Lo que pasa es que se mezclan **dos cosas distintas**:

| | Qué mide | Aquí |
|---|---|---|
| **MONOREPO** | cuántos **repositorios** hay | **uno** |
| **MONOLITO** | cuántas **unidades desplegables** hay | **dos propias** |

> **«Monolito» se predica de una unidad desplegable, no de un repositorio.**
> Tener todo junto en GitHub se llama **monorepo**, y es una decisión sobre
> cómo se guarda el código — no sobre cómo se ejecuta.

| | ¿Monolito? | Por qué |
|---|---|---|
| `api_facturas/` | **Sí** | Un proceso, un `uvicorn`, un despliegue. Los recursos viven adentro y se despliegan juntos |
| `front_flask/` | **Sí** | Un `app.py`, un proceso, un despliegue |
| **El sistema** | **No** | Son **dos** unidades que se despliegan por separado y se hablan por HTTP |

**¿Y microservicios?** No, y conviene decir por qué: faltan las tres cosas que
los definen — **base de datos propia por servicio**, **descubrimiento** y
**comunicación asíncrona**. Aquí hay una sola base, las direcciones están en
el `docker-compose.yml`, y todo es HTTP sincrónico.

> **Y no es un defecto.** Para este tamaño, partirlo agregaría problemas que
> no se tienen: transacciones distribuidas y un despliegue por servicio.

---

## 3. Los tres niveles

| Nivel | Quién | Qué decide |
|---|---|---|
| **1 · Presentación** | `front_flask/` | **Nada.** Pregunta y obedece |
| **2 · Aplicación** | `api_facturas/` | La forma de la petición y las reglas |
| **3 · Datos** | `postgres` — 12 tablas | La integridad: claves, restricciones y disparadores |

**Y el nivel 3 no solo guarda:** el esquema trae las claves foráneas y las
restricciones que **defienden las reglas aunque la API se equivoque**. Si
alguien pregunta «¿y si la API manda un cliente que no existe?», la respuesta
no es «confiamos en la API»: **la base lo rechaza**, y se puede demostrar
desde `psql`.

---

## 4. Las tres capas de la API, que no son los tres niveles

Se confunden siempre: los **niveles** son procesos; las **capas** son la
organización de uno de ellos.

```
  controllers/  ──▶  servicios/  ──▶  repositorios/  ──▶  la base de datos
    (HTTP)           (reglas)          (SQL)
```

| Carpeta | Qué hace | Qué tiene PROHIBIDO |
|---|---|---|
| `controllers/` | Traduce HTTP ↔ negocio. Lee la petición, devuelve el código | Saber SQL |
| `servicios/` | Las reglas | **Saber que existe un 404** — lanza `LookupError` |
| `repositorios/` | El SQL, y nada más | Decidir reglas de negocio |
| `models/` | La forma de lo que entra, con Pydantic | Tener lógica |

**Cada capa habla con la siguiente a través de un `Protocol`:**

```python
class IRepositorioProducto(Protocol):
    async def obtener_todos(self, limite: int) -> list[dict]: ...
```

> **`Protocol` es tipado estructural (PEP 544):** cualquier clase con esos
> métodos cumple el contrato **sin heredar de nada**. El servicio depende de
> la interfaz, nunca de una clase concreta — la **D** de SOLID.
>
> Y de ahí sale lo que más se enseña en este curso: **hay tres
> implementaciones del mismo contrato**, una por motor, y el servicio no sabe
> cuál le tocó.

---

## 5. La fábrica: el único punto que decide el motor

```python
_FABRICAS = {
    "postgres":  {"variable_cadena": "DB_POSTGRES",  "repositorios": {...}},
    "mariadb":   {"variable_cadena": "DB_MARIADB",   "repositorios": {...}},
    "sqlserver": {"variable_cadena": "DB_SQLSERVER", "repositorios": {...}},
}
```

`servicios/ensamblador.py` es **el único archivo del sistema que nombra clases
concretas**. Cambiar de motor es cambiar una variable de entorno:

```powershell
$env:DB_PROVIDER="mariadb"; docker compose up -d api-facturas
```

> **Comprobado**, no prometido: con los tres valores, `GET /api/producto`
> responde **200** y los mismos ocho productos. Los pasos están en
> [`DEMOSTRACION_MOTORES.md`](../DEMOSTRACION_MOTORES.md).
>
> **Y agregar un recurso no rompió nada:** al sumar `rol` se tocó **un bloque
> por familia** en el ensamblador — ni un `if` regado por el código.

---

## 6. El front también tiene capas

Es la parte que más sorprende, porque un front en Flask parece «una sola
cosa». No lo es:

| Archivo | Qué es | Su equivalente en la API |
|---|---|---|
| `app.py`, `rutas_*.py` | Las rutas: qué pantalla responde a cada dirección | El **controlador** |
| `cliente_api.py` | **La única pieza que habla HTTP.** Traduce todo a `(ok, datos, errores)` | El **repositorio** |
| `entidades.py` | La declaración de qué recursos hay y con qué campos | — |
| `templates/` | Lo que la persona ve | La vista |

> **`entidades.py` merece una mirada**: un solo juego de plantillas atiende a
> todas las entidades porque la entidad llega como dato, no como código
> repetido. Agregar una pantalla de CRUD es **agregar una entrada al
> diccionario**.

---

## 7. El viaje de un clic

Guardar un rol, de punta a punta:

| # | Dónde | Qué pasa |
|---|---|---|
| 1 | Navegador | Se envía el formulario a `POST /roles/nuevo` |
| 2 | `rutas_entidades.py` | La ruta de Flask recibe el formulario |
| 3 | `cliente_api.py` | Lo convierte en `POST http://api-facturas:8005/api/rol` |
| 4 | `models/rol.py` | **Pydantic valida la forma**: si falta el nombre, **422** y no llega al controlador |
| 5 | `rol_controller.py` | Traduce. No sabe SQL |
| 6 | `servicio_rol.py` | Las reglas. Un nombre de solo espacios → `ValueError` → **400** |
| 7 | `repositorio_rol_postgresql.py` | El `INSERT`, parametrizado |
| 8 | `postgres` | La clave la genera la base |

**El sobre de la respuesta, que es el contrato entre los dos procesos:**

```json
{ "tabla": "rol", "limite": 1000, "total": 5, "datos": [ ... ] }
```

> **No es una lista pelada, y es a propósito.** Un arreglo suelto no puede
> decir cuántos hay ni de qué tabla viene. Leer mal este sobre deja la
> pantalla **vacía y sin ningún error**, que es el defecto más difícil de ver.

---

## 8. Lo que se puede comprobar en cinco minutos

| Afirmación | Cómo se comprueba |
|---|---|
| Son cinco procesos | `docker compose ps` |
| El front no toca la base | Buscar `sqlalchemy` o una cadena de conexión en `front_flask/`: no hay |
| Son dos unidades desplegables | `docker compose stop api-facturas`: el front **responde** y muestra el aviso |
| El servicio no sabe de SQL | Buscar `SELECT` en `servicios/`: no hay |
| Un solo punto decide el motor | Buscar `DB_PROVIDER`: sale en el compose y en `ensamblador.py` |

---

| Qué | Dónde |
|---|---|
| Las capas y sus prohibiciones | [`SOLID_CAPAS_PATRONES.md`](SOLID_CAPAS_PATRONES.md) |
| El viaje de una petición, en detalle | [`FLUJO_DE_UNA_PETICION.md`](FLUJO_DE_UNA_PETICION.md) |
| Qué es cada contenedor | [`CONCEPTOS_DOCKER.md`](CONCEPTOS_DOCKER.md) |
| El cambio de motor, paso a paso | [`DEMOSTRACION_MOTORES.md`](../DEMOSTRACION_MOTORES.md) |
