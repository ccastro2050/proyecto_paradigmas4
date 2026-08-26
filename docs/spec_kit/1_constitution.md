# Constitución del Proyecto Paradigmas

> Principios **innegociables** que gobiernan todo el proyecto. Esta
> constitución es **permanente**: describe el sistema COMPLETO al que se llega
> al final, y no cambia entre versiones.
>
> El proyecto se construye **por versiones** (desarrollo incremental guiado por
> especificaciones): ver el [mapa de versiones](versiones/0_mapa_versiones.md).
> Cada artículo aplica desde la versión que introduce su alcance — por ejemplo,
> en la v1 solo existe `api_facturas` con PostgreSQL, así que los artículos
> sobre el front, los otros motores y docker compose son la META, no el estado
> actual.

---

## Artículo 1 — Propósito didáctico ante todo

Este proyecto existe para **enseñar paradigmas de programación y arquitectura de
software** a estudiantes universitarios. Ante cualquier disyuntiva entre "lo más
profesional" y "lo más claro para aprender", gana la claridad:

- Todo el código, comentarios, docstrings, mensajes y documentación se escriben en **español**.
- Cada archivo abre con un docstring/comentario que explica su papel en la arquitectura.
- Se prefiere código explícito y repetitivo-pero-legible sobre metaprogramación compacta.

## Artículo 2 — Arquitectura de 3 capas estricta

```
CAPA 1: FRONT (Flask, :8000)  — solo pinta HTML y llama APIs; NUNCA toca la BD
CAPA 2: API (FastAPI)        — api_facturas :8005
CAPA 3: DATOS                 — PostgreSQL | MariaDB | SQL Server (bdfacturas)
```

- El front **no importa drivers de base de datos**; solo habla HTTP con las APIs.
- Las APIs no generan HTML; solo JSON.
- Cada capa se puede reemplazar sin tocar las otras (el front funciona igual con
  las dos APIs; las APIs funcionan igual con los 3 motores).

## Artículo 3 — Independencia del motor de base de datos

- El motor activo se elige con **una sola variable**: `DB_PROVIDER`
  (`postgres` | `mariadb` | `sqlserver`). Nunca con cambios de código.
- Los tres motores contienen la **misma base de datos** (`bdfacturas_*_local`):
  mismas 12 tablas, mismos datos de ejemplo, mismos triggers y procedimientos
  almacenados, traducidos al dialecto de cada motor.
- Todo acceso a datos pasa por interfaces (Protocol) + fábrica de repositorios,
  aplicando inversión de dependencias (SOLID). Ver `docs/PRINCIPIOS_SOLID_ACID.md`.

## Artículo 4 — Un solo comando para arrancar

`docker compose up -d --build` debe dejar TODO funcionando: front, 2 APIs,
3 motores con datos, y phpMyAdmin. Sin pasos manuales, sin instalar nada local
más allá de Docker. Los estudiantes tienen máquinas heterogéneas: el entorno
vive completo en contenedores.

## Artículo 5 — Persistencia y reproducibilidad

- Los datos viven en **volúmenes** Docker (`pgdata`, `mariadbdata`, `mssqldata`):
  sobreviven a `docker compose down` y a reinicios del PC.
- `docker compose down -v` devuelve las BD a su estado original (los `init.sql`
  se re-ejecutan sobre volúmenes vacíos). Ese es el "botón de pánico" oficial.
- Los scripts de inicialización son **idempotentes o de una sola vez**: los motores
  solo los ejecutan con volumen vacío (Postgres/MariaDB) o tras verificar que la
  BD no existe (SQL Server via `sqlserver-init`).

## Artículo 6 — Convenciones fijas

| Cosa | Convención |
|---|---|
| Puertos públicos | front 8000 · · api_facturas 8005 · phpMyAdmin 8081 |
| Puertos de BD hacia el host | PostgreSQL **15435** · MariaDB **13306** · SQL Server **11433** (desplazados para no chocar con motores locales) |
| Hosts internos (entre contenedores) | `postgres:5432` · `mariadb:3306` · `sqlserver:1433` · `api-facturas:8005` |
| Credenciales BD | usuario `paradigmas` / clave `paradigmas123` (SQL Server: `sa` / `Paradigmas123!`) |
| Bases de datos | `bdfacturas_postgres_local` · `bdfacturas_mariadb_local` · `bdfacturas_sqlserver_local` |
| Nombres de código | snake_case en español; clases PascalCase; interfaces con prefijo `i_`/`I` |
| Documentación de APIs | api_facturas: `/docs` |

## Artículo 7 — Desarrollo con recarga en caliente

El código fuente se monta como volumen dentro de los contenedores
(`./front_flask:/app`, etc.) y los servidores corren con `--debug`/`--reload`:
guardar un archivo recarga la aplicación sin reconstruir imágenes. Reconstruir
(`--build`) solo es necesario cuando cambian dependencias o Dockerfiles.

## Artículo 8 — Seguridad en su justa medida académica

- Las contraseñas de usuarios de la aplicación se almacenan con **BCrypt** (nunca texto plano en código nuevo).
- Los valores SQL siempre van **parametrizados** (nunca concatenados).
- Las credenciales de infraestructura (paradigmas/paradigmas123) son públicas y
  didácticas **a propósito**: este entorno jamás se despliega a producción.
