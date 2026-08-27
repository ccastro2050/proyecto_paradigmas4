# El flujo de una petición — dónde está el GET, quién captura el body

> Documento para leer CON el código abierto. Responde las preguntas que todo
> el mundo se hace la primera vez: ¿dónde "está" el GET? ¿quién captura el
> body del POST? ¿cómo termina ejecutándose mi función del controller?

---

## 1. Lo primero: el verbo NO lo pone su código — lo manda el cliente

Cuando el navegador (o PowerShell, o Swagger) hace una petición, por la red
viaja un texto que empieza así:

```
GET /api/producto HTTP/1.1          ← un GET: verbo + ruta, sin body
```

```
POST /api/producto HTTP/1.1         ← un POST: verbo + ruta...
Content-Type: application/json

{"codigo":"PR009","nombre":"Webcam","stock":10,"valorunitario":350000}   ← ...y body
```

El verbo (GET, POST, PUT, PATCH, DELETE) **viene de afuera**. Su código no
lo declara: lo **registra** para que el framework sepa a quién llamar.

> El navegador solo sabe mandar GET desde la barra de direcciones. Para
> mandar POST/PUT/PATCH/DELETE se usa Swagger (`/docs`), PowerShell
> (`Invoke-RestMethod`), `curl` o la colección de Postman de `postman/`.

## 2. ¿Dónde está el GET? En el DECORADOR

En FastAPI usted no compara el verbo — lo **declara** con un decorador, y el
framework hace la comparación por dentro:

```python
@router.get("/producto")            # ← ESTO es "el GET de la colección"
async def listar_productos(limite: int = 1000):
    ...

@router.post("/producto")           # ← y ESTO es "el POST"
async def crear_producto(producto: Producto):
    ...
```

El decorador registra la pareja **(verbo, ruta) → función** en una tabla de
rutas. Cuando uvicorn recibe `POST /api/producto`, FastAPI busca esa pareja
en la tabla y llama `crear_producto(...)`. Su función es "el POST"
únicamente porque quedó registrada bajo ese verbo.

> Si programara **sin framework** (PHP puro, o el módulo `http` de Node),
> esa comparación la escribiría usted a mano: `if metodo == "POST" and
> ruta == "/api/producto": ...`. FastAPI la esconde — el decorador es
> azúcar sobre esa misma tabla de decisiones.

La cadena completa del registro está en dos archivos:

| Pieza | Archivo | Línea clave |
|---|---|---|
| Las 6 rutas de producto | `controllers/producto_controller.py` | `router = APIRouter(prefix="/api", tags=["Producto"])` + un decorador por endpoint |
| El router se conecta a la app | `main.py` | `app.include_router(router)` |

## 3. Las tres capturas (FastAPI las hace por la FIRMA de la función)

Aquí está la diferencia grande con programar a mano: usted no "lee" nada —
**declara parámetros tipados y FastAPI los llena** mirando de dónde viene
cada uno:

| Qué se captura | Cómo se declara | Ejemplo real |
|---|---|---|
| **Parámetro de ruta** | Aparece en la ruta entre llaves Y como argumento | `@router.get("/producto/{codigo}")` + `def obtener_producto(codigo: str)` |
| **Query string** | Argumento con valor por defecto que NO está en la ruta | `def listar_productos(limite: int = 1000)` captura `?limite=3` |
| **El body JSON** | Argumento tipado con un modelo Pydantic | `def crear_producto(producto: Producto)` |

Lo del body es lo más importante: FastAPI lee el JSON crudo, lo **valida
contra el modelo Pydantic** (tipos, obligatorios, `ge=0`) y le entrega a su
función un objeto `Producto` ya construido. Si el body no cumple, responde
**422 él solo** — su función del controller **jamás llega a ejecutarse**.
En un GET no hay body y no se declara ninguno.

## 4. El viaje completo de un POST, capa por capa

`POST /api/producto` con `{"codigo":"PR009","nombre":"Webcam","stock":10,"valorunitario":350000}`:

```
1. uvicorn           recibe el texto HTTP y se lo pasa a FastAPI
2. FastAPI           busca (POST, /api/producto) en la tabla de rutas
3. FastAPI/Pydantic  valida el body contra el modelo Producto
      ├─ ¿inválido?  → responde 422 con la lista de errores y AQUÍ TERMINA
      └─ ¿válido?    → llama crear_producto(producto)
4. producto_controller.crear_producto
      try: servicio.crear(producto.model_dump()) …
5. ServicioProducto.crear      (reglas de negocio; no conoce HTTP)
6. RepositorioProductoPostgreSQL.crear
      INSERT INTO producto (...) VALUES (:codigo, :nombre, ...)  ← parametrizado
7. PostgreSQL        inserta la fila (y aplica SUS reglas: PK, NOT NULL…)
8. La respuesta sube: el controller responde 200 {estado, mensaje}
```

Si algo falla en 5, 6 o 7, la excepción sube hasta el `try/except` del
controller, que la traduce a un código HTTP:

| Qué pasó | Excepción | Código |
|---|---|---|
| El body venía mal formado | (no llega al controller: la atrapa Pydantic) | **422** |
| Regla de negocio rota (límite ≤ 0, PATCH sin campos) | `ValueError` | **400** |
| El código no existe en la tabla | `LookupError` | **404** |
| La BD rechazó (código duplicado, conexión caída…) | cualquier otra | **500** |


**El mismo viaje, como diagrama de flujo** — fíjese en que la gracia son
las SALIDAS TEMPRANAS: cada capa puede terminar la película sin molestar a
las de abajo:

```mermaid
flowchart TD
    A["1. uvicorn recibe<br/>el texto HTTP"] --> B["2. FastAPI encuentra<br/>POST /api/producto<br/>en la tabla de rutas"]
    B --> C{"3. ¿el body cumple<br/>el modelo Pydantic?"}
    C -->|"NO"| E422["422 con la lista de errores.<br/>AQUÍ TERMINA: su código de<br/>negocio nunca se enteró"]
    C -->|"sí"| D["4. el controlador<br/>(con su try/catch)"]
    D --> E["5. el SERVICIO:<br/>reglas de negocio<br/>(no conoce HTTP)"]
    E -->|"regla rota:<br/>ValueError"| E400["400 con su sobre:<br/>estado, mensaje, detalle"]
    E -->|"pasa"| F["6. el REPOSITORIO:<br/>INSERT parametrizado<br/>con :codigo, :nombre, ..."]
    F --> G{"7. ¿la base de<br/>datos aceptó?"}
    G -->|"PK duplicada · NOT NULL<br/>· conexión caída"| E500["500 con el error del<br/>motor en el detalle"]
    G -->|"sí"| OK["8. la respuesta SUBE<br/>por las mismas capas:<br/>200 estado, mensaje"]
```

**Guía de lectura:** el camino feliz es la columna del centro; cada rombo
es una defensa y cada salida lateral, un código HTTP distinto. Por eso el
error también es contrato: se sabe QUIÉN lo decide (la frontera → 422, el
servicio → 400, la BD → 500) y QUIÉN le pone el número (el controlador).


## 5. El viaje de un GET (más corto: no hay body ni validación de forma)

`GET /api/producto/PR001`:

```
1. FastAPI busca (GET, /api/producto/{codigo}) y extrae codigo="PR001"
2. producto_controller.obtener_producto("PR001")
3. ServicioProducto.obtener   pide al repositorio; si llega None → lanza
                              LookupError (el except la vuelve 404)
4. RepositorioProductoPostgreSQL   SELECT ... WHERE codigo = :codigo
5. La fila vuelve como dict y sale como JSON
```


**Y el del GET, en diagrama de flujo** (la defensa aquí es una sola: ¿existe?):

```mermaid
flowchart LR
    A["GET /api/<br/>producto/PR001"] --> B["controlador"] --> S["servicio"] --> R["repositorio:<br/>SELECT ... WHERE<br/>codigo = :codigo"]
    R --> E{"¿hay fila?"}
    E -->|"sí"| OK["200: el producto<br/>en JSON"]
    E -->|"no"| N["el servicio lanza<br/>'no existe'<br/>(LookupError)"] --> C404["el controlador<br/>la traduce: 404"]
```


## 6. Véalo usted mismo (5 minutos)

En la terminal de VS Code (PowerShell), con el proyecto corriendo
(`docker compose up -d`):

```powershell
# GET (el navegador también sirve para estos dos)
Invoke-RestMethod "http://localhost:8005/api/producto"
Invoke-RestMethod "http://localhost:8005/api/producto/PR001"

# POST — crear
Invoke-RestMethod -Method Post -Uri "http://localhost:8005/api/producto" -ContentType "application/json" -Body '{"codigo":"PR009","nombre":"Webcam","stock":10,"valorunitario":350000}'

# PUT con body incompleto → error 422 (PUT exige TODO)
Invoke-RestMethod -Method Put -Uri "http://localhost:8005/api/producto/PR009" -ContentType "application/json" -Body '{"stock":25}'

# PATCH con el MISMO body → 200 (PATCH es parcial)
Invoke-RestMethod -Method Patch -Uri "http://localhost:8005/api/producto/PR009" -ContentType "application/json" -Body '{"stock":25}'

# DELETE — limpiar
Invoke-RestMethod -Method Delete -Uri "http://localhost:8005/api/producto/PR009"
```

> Si está probando **SU reconstrucción** (la de la [GUIA_IA](GUIA_IA.md),
> que corre con puertos +100): cambie `8005` por `8105`.

La pareja PUT/PATCH con el mismo body es la lección más importante del
flujo: el MISMO dato, dos verbos, dos resultados — porque cada verbo tiene
su semántica y la API la hace cumplir. Y todo esto también se puede recorrer
con clics en **http://localhost:8005/docs** (Swagger) o con la colección de
[postman/](../postman/README.md).
