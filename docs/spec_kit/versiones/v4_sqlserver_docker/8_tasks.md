# Tareas — Versión 4: orden de construcción por fases verificables

> Cada fase termina en un estado COMPROBABLE. No avance con una fase en
> rojo. El detalle de diseño está en [3_plan.md](3_plan.md).

---

## Fase 0 — Punto de partida

- [ ] La v3 corre y pasa su regresión doble (tag `v3` presente).

**Verificar:** `curl http://localhost:8005/` → `"version":"v3"`.

## Fase 1 — El motor nuevo en el compose (sin tocar la API)

- [ ] `db/bdfacturas_sqlserver.sql` (cópielo del proyecto del curso — es
      dato) y `db/init_sqlserver.sh`.
- [ ] `docker-compose.yml`: `sqlserver` (2022, :11435, healthcheck con
      sqlcmd y `start_period`) + `sqlserver-init` (entrypoint al .sh,
      `restart: "no"`).
- [ ] `docker compose up -d` — la API sigue en v3: nada se rompe.

**Verificar:**
```powershell
docker compose logs sqlserver-init | Select-String "correctamente"
docker compose exec sqlserver /opt/mssql-tools18/bin/sqlcmd -S localhost -U sa -P "Paradigmas123!" -C -d bdfacturas_sqlserver_local -Q "SELECT COUNT(*) FROM producto"   # 8
```

## Fase 2 — La imagen aprende ODBC y nacen los repositorios

- [ ] `Dockerfile`: msodbcsql18 + unixodbc · `requirements.txt`: aioodbc
      · `docker compose up -d --build`.
- [ ] Los 5 moldes calcados con `TOP (:limite)` ([plan §2](3_plan.md)).
- [ ] `repositorio_factura_sqlserver.py`: el lote
      DECLARE/EXEC/SELECT con `SET NOCOUNT ON` + traducción por patrón
      con limpieza del prefijo ODBC ([plan §3](3_plan.md)).

**Verificar:** la API arranca sin errores de import.

## Fase 3 — El bloque en la fábrica

- [ ] `ensamblador.py`: el bloque `"sqlserver"` en `_FABRICAS` + imports.
      NADA más cambia en el archivo.
- [ ] `docker-compose.yml`: `DB_SQLSERVER` + depends_on del init.
- [ ] `main.py`: `version="v4"`.
- [ ] `pruebas/prueba_capas.py`: el tercer dialecto en la prueba de la
      fábrica.

**Verificar:** `docker compose exec api-facturas python
pruebas/prueba_capas.py` → todo OK, incluida la fábrica sqlserver.

## Fase 4 — Verificación total y cierre

- [ ] **Regresión TRIPLE** ([7_quickstart.md](7_quickstart.md) §2):
      v1+v2 contra postgres → mariadb → sqlserver, sin recompilar.
- [ ] `git diff v3 --stat` respeta la frontera (criterio 4).
- [ ] Postman: nota de la v4 (tercer motor) · mapa y README · commit +
      tag `v4` + push.

**Verificar:** los 5 criterios de [2_spec.md](2_spec.md) §5 en verde.
