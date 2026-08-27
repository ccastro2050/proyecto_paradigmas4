# Programación asincrónica en la web — qué resuelve y qué pasa si no se usa

> Documento conceptual del curso. La pregunta que responde: **¿por qué el
> código de una API web no puede quedarse ESPERANDO, y qué herramientas da
> el lenguaje para no hacerlo?**

---

## 1. El dato que lo explica todo: una petición web casi no COMPUTA — ESPERA

Cuando su API atiende `GET /api/producto`, ¿en qué gasta el tiempo?

```mermaid
flowchart LR
    subgraph VIDA["La vida de una petición (~42 ms)"]
        CPU1["validar y preparar<br/>~1 ms de CPU"] --> ESPERA["ESPERAR a la base de datos<br/>~40 ms SIN usar la CPU<br/>(viaje de red + consulta)"] --> CPU2["armar el JSON<br/>~1 ms de CPU"]
    end
```

**El 95% del tiempo, el servidor no está trabajando: está esperando** a la
BD, al disco o a otra API. La pregunta de diseño es: mientras una petición
espera, ¿qué hace el servidor con las demás? Las respuestas posibles son
tres: bloquearse (el problema), liberar el hilo (asincronía) o multiplicar
procesos (el modelo clásico de PHP). Este documento recorre las tres.

## 2. El problema: el mesero que se queda mirando la cocina

Modelo **síncrono bloqueante** con pocos hilos — el hilo que atiende la
petición se queda parado hasta que la BD responda:

```mermaid
sequenceDiagram
    autonumber
    actor C1 as Cliente 1
    actor C2 as Cliente 2
    participant S as Servidor (1 hilo)
    participant BD as Base de datos
    C1->>S: GET /api/producto
    S->>BD: SELECT ... (tarda 40 ms)
    Note over S: el hilo se queda MIRANDO la cocina:<br/>no computa nada, pero está OCUPADO
    C2->>S: GET /api/producto/PR001
    Note over C2: Cliente 2 ESPERA EN LA FILA...<br/>aunque el servidor esté ocioso
    BD-->>S: filas
    S-->>C1: 200
    S->>BD: SELECT ... (ahora sí, el de Cliente 2)
    BD-->>S: fila
    S-->>C2: 200 (llegó tarde sin culpa de la BD)
```

**Qué se daña si no se resuelve** (los síntomas reales, en orden de
aparición):

1. **Latencia en fila india:** los usuarios no esperan SU consulta —
   esperan la suma de las de adelante.
2. **Hilos/workers agotados:** con 200 hilos y consultas de 2 segundos,
   el usuario 201 recibe timeout — con la CPU al 5%.
3. **Caídas en cascada:** los clientes reintentan, la fila crece, los
   timeouts se propagan al front... el clásico "se cayó el sistema" que
   en realidad es "se sentó a esperar".
4. **Escalar a punta de plata:** como cada petición secuestra un
   hilo/worker, la salida es comprar más servidores — pagar con
   infraestructura lo que era un problema de diseño.

## 3. La solución asincrónica: soltar el hilo mientras se espera

La idea completa en una frase: **cuando la operación es de
entrada/salida (I/O), el hilo la INICIA, se va a atender a otro, y VUELVE
cuando el resultado está listo.** Eso es `await`:

```mermaid
sequenceDiagram
    autonumber
    actor C1 as Cliente 1
    actor C2 as Cliente 2
    participant S as Servidor (el MISMO hilo)
    participant BD as Base de datos
    C1->>S: GET /api/producto
    S->>BD: SELECT ... (await: inicia y SUELTA)
    Note over S: el hilo queda LIBRE
    C2->>S: GET /api/producto/PR001
    S->>BD: SELECT ... (await: inicia y SUELTA)
    BD-->>S: filas del Cliente 1 listas
    S-->>C1: 200
    BD-->>S: fila del Cliente 2 lista
    S-->>C2: 200 (nadie hizo fila en el servidor)
```

Las dos esperas de BD ocurren **superpuestas** y el mismo hilo atendió a
ambos clientes. No se volvió más rápida ninguna consulta — se dejó de
desperdiciar la espera. Eso es lo que la asincronía resuelve: **ocupar la
espera, no acelerar el trabajo.**

## 4. Asincronía NO es paralelismo (la confusión clásica)

| | Asincronía (concurrencia por I/O) | Paralelismo (varios núcleos) |
|---|---|---|
| Para qué sirve | Esperas: BD, red, disco | Cómputo pesado: cifrar, comprimir, calcular |
| Cuántos hilos | Pocos (incluso UNO) que no se bloquean | Varios, trabajando a la vez |
| La imagen | UN mesero que atiende 10 mesas mientras la cocina trabaja | 10 cocineros picando a la vez |
| En una API web | La herramienta correcta (la API casi solo espera) | Rara vez el problema de una API CRUD |

## 5. Cómo se ve en ESTE proyecto (código real)

Toda la cadena de la API es asincrónica — fíjese en que el `async`/`await`
recorre las TRES capas:

```python
# Controlador (FastAPI): la función del endpoint es una corrutina
@router.get("/api/producto")
async def listar(limite: int = 1000):
    return await servicio.obtener_todos(limite)

# Servicio: valida y DELEGA — el await pasa de largo
async def obtener_todos(self, limite: int) -> list[dict]:
    if limite <= 0:
        raise ValueError("El límite debe ser mayor que cero.")
    return await self._repositorio.obtener_todos(limite)

# Repositorio: aquí ocurre la espera REAL (la BD) — y el await la libera
async def obtener_todos(self, limite: int) -> list[dict]:
    async with self._engine.connect() as conexion:
        resultado = await conexion.execute(
            text("SELECT * FROM producto LIMIT :limite"), {"limite": limite})
        ...
```

Mientras ese `await conexion.execute(...)` espera a la base de datos, el
event loop de uvicorn atiende OTRAS peticiones con el mismo y único hilo.

**Los errores clásicos en Python (lo que NO se hace):**

1. **Olvidar el `await`:** `servicio.obtener_todos(5)` sin await no ejecuta
   nada — devuelve una corrutina sin arrancar (warning: *coroutine was
   never awaited*) y el endpoint responde basura.
2. **Bloquear el event loop:** un `time.sleep(5)` o una librería de BD
   síncrona dentro de un `async def` CONGELA el loop entero — ninguna otra
   petición avanza. Lo lento se espera con `await` (asyncio.sleep, driver
   async) o se saca del loop.
3. **Async de mentiras:** declarar `async def` y adentro usar un driver
   síncrono. El sistema "compila", pero es el diagrama 1 disfrazado del 2.

## 6. Referencias

1. MDN — *Asynchronous JavaScript* (los conceptos, aplicables a cualquier
   stack): <https://developer.mozilla.org/es/docs/Learn_web_development/Extensions/Async_JS>
2. Python — `asyncio` (el event loop): <https://docs.python.org/es/3/library/asyncio.html>
   y FastAPI — *Async/await*: <https://fastapi.tiangolo.com/es/async/>
3. Microsoft — *Asynchronous programming with async and await* (C#):
   <https://learn.microsoft.com/dotnet/csharp/asynchronous-programming/>
4. PHP — FPM (el modelo por procesos): <https://www.php.net/manual/es/install.fpm.php>
   y Fibers (PHP 8.1+): <https://www.php.net/manual/es/language.fibers.php>
5. En este repositorio: [FLUJO_DE_UNA_PETICION.md](FLUJO_DE_UNA_PETICION.md)
   (el viaje completo por las capas) y el código de la API, donde este
   documento se ve funcionando.
