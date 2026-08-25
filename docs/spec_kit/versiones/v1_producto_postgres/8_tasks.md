# Tareas — Versión 1: api_facturas con producto + PostgreSQL

> **Versión 1** · El orden de construcción, partiendo de CERO. Cada fase termina
> en algo **verificable**. Requisitos: [2_spec.md](2_spec.md) · técnica:
> [3_plan.md](3_plan.md) · contratos: [6_contracts.md](6_contracts.md) ·
> validación final: [7_quickstart.md](7_quickstart.md).

---

## Fase 0 — Base de datos y esqueleto
- [ ] Copiar a `db/init.sql` el script **provisto** con esta versión (la BD
      `bdfacturas` COMPLETA — no se escribe ni se genera con IA; ver
      [5_data_model.md](5_data_model.md) §1).
- [ ] Crear el `docker-compose.yml` con el servicio `postgres` (volumen
      `pgdata`, `db/init.sql` montado, puerto 15435, healthcheck — ver
      [3_plan.md](3_plan.md) §5) y levantarlo: `docker compose up -d`.
- [ ] Crear la carpeta `api_facturas/` con subcarpetas `models/`,
      `controllers/`, `servicios/` (`abstracciones/`), `repositorios/`
      (`abstracciones/`) y sus `__init__.py`.
- [ ] `requirements.txt`: fastapi, uvicorn, sqlalchemy[asyncio], asyncpg,
      greenlet, pydantic.
- [ ] Entorno virtual + `pip install -r requirements.txt` (para desarrollar
      las fases con `uvicorn` local; la entrega final corre en Docker).

**Verificar:** `python -c "import fastapi, sqlalchemy, asyncpg"` no falla, y un
cliente SQL ve las **12 tablas** de `bdfacturas` con **8 filas en `producto`**.

## Fase 1 — Modelos Pydantic (uno por semántica HTTP)
- [ ] `models/producto.py`: `Producto` (POST, todos obligatorios),
      `ProductoReemplazo` (PUT, obligatorios sin código) y
      `ProductoActualizar` (PATCH, todos opcionales) —
      según [3_plan.md](3_plan.md) §4.2.

**Verificar:** en un REPL, `Producto(codigo="X", nombre="Y", stock=-1,
valorunitario=1)` lanza `ValidationError`, y `ProductoActualizar(stock=7)`
es válido.

## Fase 2 — Contratos (interfaces)
- [ ] `repositorios/abstracciones/i_repositorio_producto.py`: Protocol con los
      5 métodos async (`obtener_todos(limite)`, `obtener_por_codigo`, `crear`,
      `actualizar` — lo usan PUT y PATCH — y `eliminar`).
- [ ] `servicios/abstracciones/i_servicio_producto.py`: Protocol del servicio.

**Verificar:** los archivos importan sin errores (son solo contratos).

## Fase 3 — Repositorio PostgreSQL
- [ ] `repositorios/repositorio_producto_postgresql.py`: engine async perezoso,
      los 5 métodos con SQL parametrizado de [3_plan.md](3_plan.md) §4.4,
      `Decimal` → float al serializar.

**Verificar:** un script suelto instancia el repositorio con `DB_POSTGRES` y
lista los 8 productos.

## Fase 4 — Servicio (y la prueba de capas)
- [ ] `servicios/servicio_producto.py`: recibe `IRepositorioProducto` por
      constructor; valida código no vacío; traduce "no encontrado" a
      `LookupError`.
- [ ] `servicios/ensamblador.py`: `crear_servicio_producto()` — las 3 líneas de
      [3_plan.md](3_plan.md) §4.3 (sin fábrica multi-motor: eso es v3).

**Verificar (criterio 6 de la spec):** un script instancia `ServicioProducto`
con un **repositorio falso en memoria** (una clase con los 5 métodos sobre un
dict) y hace crear/listar/eliminar SIN PostgreSQL corriendo. Si esto funciona,
las capas quedaron bien.

## Fase 5 — Controller y aplicación
- [ ] `controllers/producto_controller.py`: los 6 endpoints de producto de
      [6_contracts.md](6_contracts.md) — GET listar (con query `limite`),
      GET por código, POST, **PUT (reemplazo completo)**, **PATCH (parcial)**
      y DELETE — con la traducción de excepciones de [3_plan.md](3_plan.md)
      §4.5 (ValueError→400, LookupError→404, resto→500) y el 204 para lista
      vacía.
- [ ] `main.py`: app FastAPI (`title="API Facturas"`, `version="v1"`),
      `include_router(prefix="/api")`, endpoint `/` de diagnóstico.

**Verificar:** `uvicorn main:app --port 8005 --reload` y en `/docs` probar:
listar (200 con 8 y `?limite=3` con 3), obtener PR001 (200), PR999 (404),
POST inválido (422), y el contraste PUT vs PATCH con `{"stock": 7}`
(422 vs 200).

## Fase 6 — Docker: un solo comando
- [ ] `api_facturas/Dockerfile`: `python:3.12-slim`, `requirements.txt` +
      `pip install` primero (caché de capas), luego el código, `CMD uvicorn`.
- [ ] Agregar al `docker-compose.yml` el servicio `api-facturas`: `build:`,
      código montado como volumen + `--reload`, puerto 8005, `DB_POSTGRES`
      con el host interno `postgres:5432`, y `depends_on` con
      `condition: service_healthy` ([3_plan.md](3_plan.md) §5).

**Verificar:** `docker compose down` y luego `docker compose up -d --build`
— UN comando deja BD y API funcionando (criterio 1 de la spec); guardar un
`.py` recarga la API dentro del contenedor.

## Fase 7 — Cierre de la versión
- [ ] Correr el smoke test completo de [7_quickstart.md](7_quickstart.md) §3 —
      equivale a los 6 criterios de aceptación de [2_spec.md](2_spec.md) §5.
- [ ] `.gitignore` (`__pycache__/`, `.venv/`, `.env*`).
- [ ] Commit y tag `v1`.

**La v1 está TERMINADA.** Solo ahora se escribe la spec de la v2
([mapa de versiones](../0_mapa_versiones.md)).
