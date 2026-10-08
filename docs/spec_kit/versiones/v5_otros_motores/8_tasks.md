# Tareas — Versión 5: orden de construcción por fases verificables

> Cada fase termina en un estado COMPROBABLE. No avance con una fase en
> rojo. El detalle de diseño está en [3_plan.md](3_plan.md).

---

## Fase 0 — Punto de partida

- [ ] La v3 corre y pasa su smoke test (tag `v3` presente).
- [ ] `git diff v3` limpio (se parte de la versión cerrada).

**Verificar:** diagnóstico responde `"version":"v3"`.

## Fase 1 — El motor nuevo en el compose (sin tocar la API)

- [ ] `db/bdfacturas_mariadb.sql` (cópielo del proyecto del curso — es
      dato, no código a generar).
- [ ] `docker-compose.yml`: el servicio `mariadb` (`mariadb:16-alpine`,
      :13335, healthcheck con `pg_isready`), con el `.sql` **montado en
      `/docker-entrypoint-initdb.d/`**.
- [ ] `docker compose up -d` — la API sigue en v3 contra PostgreSQL:
      **nada se rompe por agregar contenedores**.

> **Aquí NO hace falta un script de arranque, y conviene decir por qué**,
> porque en el proyecto del curso sí lo hay y se copia sin pensar: la imagen
> de **MariaDB ejecuta sola** todo lo que encuentre en
> `/docker-entrypoint-initdb.d/` la primera vez que nace el volumen. La de
> **PostgreSQL no hace eso** — por eso el proyecto del curso lleva un script
> de arranque y un servicio aparte que lo ejecuta, y aquí no hay ninguno de
> los dos.
>
> Dos motores, dos formas de sembrar. Es el tipo de diferencia que esta
> versión existe para mostrar.

**Verificar:**
```powershell
# que el contenedor este sano
docker compose ps mariadb

# y que la semilla haya entrado: 8 productos
docker compose exec mariadb psql -U mariadb -d bdfacturas_mariadb_local -c "SELECT COUNT(*) FROM producto;"
```

> **`psql` no se llama como `sqlcmd`.** No lleva `-S`, ni `-U sa`, ni `-P` con
> la clave en la línea: el usuario es `mariadb`, la base de datos va en `-d` y la
> consulta en `-c`. La clave la toma de la variable que el propio contenedor
> ya tiene.

## Fase 2 — Los repositorios MariaDb (el calco mecánico)

- [ ] Paquete **SQLAlchemy** en `requirements.txt`
      (+ recrear el contenedor para que restaure).
- [ ] Los 10 repositorios calcados (todos menos factura): tabla de
      traducción del [plan §2](3_plan.md) — `Sql*`, `TOP (@limite)` al
      principio, resto idéntico. BCrypt intacto en el de usuario.
- [ ] `RepositorioFacturaMariaDb`: `CommandType.StoredProcedure` +
      `@p_resultado OUTPUT` + traducción por número y patrón
      ([plan §3](3_plan.md)).

**Verificar:** compila (`docker compose logs api-facturas` sin errores).
Nada los usa todavía — el ensamblador sigue en PostgreSQL.

## Fase 3 — La fábrica

- [ ] `servicios/ensamblador.py`: un `crear_servicio_X()` por recurso, y el
      diccionario `_FABRICAS` con una familia por motor.
- [ ] `servicios/fabrica_postgres.py` y `servicios/fabrica_maria_db.py`.
- [ ] `pruebas/programa.py`: criterio 5 (cada fábrica entrega SU
      dialecto, con cadenas de mentira — construir no conecta).

**Verificar:** `docker compose exec api-facturas uvicorn main:app --reload --project
pruebas` → todos los criterios OK.

## Fase 4 — El ensamblador con interruptor

- [ ] `las variables del compose`: cadena `MariaDb` + clave `Motor`
      (default local `postgres`).
- [ ] `docker-compose.yml`: variables `Motor: ${DB_PROVIDER:-postgres}` y
      `ConnectionStrings__MariaDb` en la API + depends_on del init.
- [ ] `main.py`: el switch de fábricas + los 11 registros vía fábrica
      + diagnóstico `"version":"v5"` con `"motor"`.

**Verificar:** `GET /` → `"motor":"postgres"` · con
`$env:DB_PROVIDER="mariadb"` y recrear la API → `"motor":"mariadb"`.

## Fase 5 — Verificación total y cierre

- [ ] **Regresión doble completa** ([7_quickstart.md](7_quickstart.md)
      §2): v1+v2+v3 contra postgres, interruptor, v1+v2+v3 contra
      mariadb.
- [ ] Errores de negocio idénticos en ambos motores (criterio 3).
- [ ] `git diff v3 --stat` respeta la frontera (criterio 4).
- [ ] Colección Postman: nota de la v5 (mismos endpoints, campo `motor`).
- [ ] Commit + tag `v5` + push.

**Verificar:** los 5 criterios de [2_spec.md](2_spec.md) §5 en verde.
