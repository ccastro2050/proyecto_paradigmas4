# Tareas — Versión 1: las seis tablas sin FK, con su interfaz gráfica

> **Versión 1** · El orden de construcción, partiendo de CERO. Cada fase
> termina en algo **verificable**. Requisitos: [2_spec.md](2_spec.md) ·
> técnica: [3_plan.md](3_plan.md) · contratos: [6_contracts.md](6_contracts.md) ·
> validación final: [7_quickstart.md](7_quickstart.md).

---

## Fase 0 — Base de datos y esqueleto
- [ ] Copiar a `db/` el archivo **provisto** con esta versión:
      `init.sql` (la BD completa en dialecto PostgreSQL —
      no se escribe ni se genera con IA; ver [3_plan.md](3_plan.md) §4.6).
- [ ] Crear el `docker-compose.yml` con el servicio `postgres` (imagen
      16-alpine, volumen `pgdata`, puerto 11463, healthcheck con
      pg_isready, y el script montado en `/docker-entrypoint-initdb.d/`)
      — ver [3_plan.md](3_plan.md) §5. Levantar: `docker compose up -d`.
- [ ] Crear `api_facturas/` con subcarpetas `models/`, `models/`, `controllers/`,
      `servicios/`, `repositorios/`, `excepciones.py` y `pruebas/`.

**Verificar:** `docker compose ps` muestra `mariadb (healthy)`; un
cliente SQL a `localhost,11463` (usuario `sa`) ve las **12 tablas**
y `SELECT count(*) FROM producto` da **8**.

## Fase 1 — El proyecto .NET y el modelo Producto (la clase entidad)
- [ ] `requirements.txt`: proyecto Web de .NET 10, paquete
      `SQLAlchemy`, y la exclusión de `pruebas/**`.
- [ ] `las variables del compose` con la cadena de conexión (default
      `localhost,11463` para correr sin Docker).
- [ ] `models/producto.py`: la clase entidad con las 4 propiedades
      tipadas `{ get; set; }` (`Codigo` string, `Nombre` string, `Stock`
      int, `Valorunitario` decimal). En Python, las propiedades SON los
      getters/setters del lenguaje.

**Verificar:** `pip install -r requirements.txt` compila sin errores.

## Fase 2 — Las peticiones por verbo (la frontera de entrada) y la excepción
- [ ] `models/producto_crear.py` (POST: todo obligatorio, con código),
      `models/producto_reemplazo.py` (PUT: todo obligatorio, sin código) y
      `models/producto_actualizar.py` (PATCH: todo opcional) — con las
      anotaciones y mensajes de [3_plan.md](3_plan.md) §4.2.
- [ ] `excepciones.py` con `NoEncontradoError`: la excepción que el
      controller traducirá a 404.

**Verificar:** `pip install -r requirements.txt` compila sin errores.

## Fase 3 — Contratos (interfaces) y repositorio PostgreSQL
- [ ] `repositorios/i_repositorio_producto.py`: interface con los 5 métodos
      async ([3_plan.md](3_plan.md) §4.1).
- [ ] `servicios/i_servicio_producto.py`: interface del servicio.
- [ ] `repositorios/repositorio_producto_postgresql.py`: SQLAlchemy (solo como ejecutor, con text()) (`QueryAsync`/`ExecuteAsync`) con los SQL
      de [3_plan.md](3_plan.md) §4.4 — `LIMIT @limite`, parámetros `@`,
      conexión por operación con `await using`, y el UPDATE con SET
      dinámico de lista blanca.

**Verificar:** `pip install -r requirements.txt` compila sin errores.

## Fase 4 — Servicio (y la prueba de capas)
- [ ] `servicios/servicio_producto.py`: recibe `IRepositorioProducto` por
      constructor; valida reglas de negocio (`limite > 0`, código no
      vacío, PATCH sin campos → `ArgumentException`); traduce "no existe"
      a `NoEncontradoExcepcion`.
- [ ] `pruebas/PruebaCapasrequirements.txt` (consola, con ProjectReference a la
      API) y `pruebas/programa.py`: el servicio con un **repositorio falso
      en memoria** (una clase `: IRepositorioProducto` sobre un
      diccionario) — crear/listar/obtener/actualizar/eliminar y las
      excepciones, SIN PostgreSQL.

**Verificar (criterio 6):** `uvicorn main:app --reload --project pruebas` termina con
`CRITERIO 6 OK…`.

## Fase 5 — Controller y main.py
- [ ] `controllers/producto_controller.py`: `[Route("api/producto")]`, los 6
      métodos con sus atributos de verbo, cada uno con su try/catch
      ([3_plan.md](3_plan.md) §4.5) y el 204 para lista vacía.
- [ ] `main.py`: el ENSAMBLADOR (los dos AddScoped), la respuesta 422
      personalizada (`InvalidModelStateResponseFactory` → `{estado,
      mensaje, errores}`), **Swagger (lo genera FastAPI solo)** (`AddSwagger (lo genera FastAPI solo)Gen` + `UseSwagger (lo genera FastAPI solo)` +
      `UseSwagger (lo genera FastAPI solo)UI`), el `GET /` de diagnóstico y `MapControllers`.

**Verificar:** con la BD arriba y `uvicorn main:app --reload`, probar: listar (200 con 8 y
`?limite=3` con 3), obtener PR001 (200), PR999 (404), POST inválido (422
con `errores[]`), y el contraste PUT vs PATCH con `{"stock": 99}` (422 vs
200).

## Fase 6 — LA INTERFAZ GRÁFICA (la otra mitad de la versión)

El front en **Flask (Jinja2) / .NET 10**, en `front_flask/`, en su propio
contenedor y en el puerto **8046**.

| Qué se escribe | Dónde |
|---|---|
| El `requirements.txt` **sin un solo paquete de datos** | `requirements.txt` |
| La clase `Producto` **del front** | `models/producto.py` |
| `ServicioProducto`: el único sitio que sabe de HTTP | `servicios/servicio_producto.py` |
| El cascarón y el menú | `Components/App.html` · `Routes.html` · `Layout/` |
| La interfaz gráfica del recurso | `Components/Pages/Productos.html` |
| Bootstrap **servido desde el repositorio** | `wwwroot/lib/bootstrap/` |
| El CSS del proyecto, **encima** de Bootstrap | `wwwroot/app.css` |

**Tres cosas que se van a querer hacer y no se deben:**

| | Por qué no |
|---|---|
| **Compartir la clase `Producto`** con una referencia de proyecto | Están las dos en Python, así que *funcionaría*. Ata los dos procesos: un cambio interno de la API rompería el front sin que nadie tocara el contrato |
| **Servir las páginas desde la misma API** | Son dos procesos, y eso hay que poder demostrarlo apagando uno |
| **Meter Bootstrap por CDN** | Bootstrap si, el CDN no: se copia a `wwwroot/lib/`. Un front que necesita internet para verse bien no arranca en un salón sin red |

**Verificación:** `http://localhost:8046/productos` lista los 8 productos, se
crea uno desde la interfaz gráfica, y **los dos botones de guardar** hacen cosas
distintas (criterios 7 a 9 de [2_spec.md](2_spec.md)).

## Fase 7 — La prueba que separa los dos procesos

```powershell
docker compose stop api-facturas
```

Recargue `http://localhost:8046/productos`.

**Verificación:** el menú sigue, hay un aviso de que no se pudo conectar, y
**no hay ni una fila**. Es el criterio 10, y es el único que no se puede
simular: o los dos procesos están separados, o no.

Después, `docker compose start api-facturas` y la interfaz gráfica vuelve a listar.

## Fase 8 — Docker: un solo comando
- [ ] `api_facturas/Dockerfile`: imagen `python:3.12-slim`, `uvicorn main:app --reload`,
      el puerto 8005 y `--reload-dir /app` (el sondeo que hace falta dentro
      del contenedor para que detecte los cambios del volumen montado).
- [ ] Agregar al `docker-compose.yml` el servicio `api-facturas`: `build:`,
      código montado + `bin/` y `obj/` en volúmenes anónimos, puerto 8005,
      variable `ConnectionStrings__Postgres` con el host interno
      `mariadb:5432`, y `depends_on` de `mariadb` con
      `condition: service_healthy`.

**Verificar:** `docker compose down` y luego `docker compose up -d --build`
— UN comando deja BD y API funcionando (criterio 1); editar un `.py`,
guardar, y verificar que recompila y reinicia solo.

## Fase 9 — Cierre de la versión
- [ ] Correr el smoke test completo de [7_quickstart.md](7_quickstart.md)
      §2 — equivale a los 6 criterios de aceptación de
      [2_spec.md](2_spec.md) §5.
- [ ] `.gitignore` (`bin/`, `obj/`, `*.session.sql`) y `.gitattributes`
      (`*.sh` con LF).
- [ ] Commit y tag `v1`.

**La v1 está TERMINADA.** Solo ahora se escribe la spec de la v2
([mapa de versiones](../0_mapa_versiones.md)).
