# Tareas — Versión 3: orden de construcción por fases verificables

> Cada fase termina en un estado COMPROBABLE. No avance con una fase en
> rojo. El detalle de diseño está en [3_plan.md](3_plan.md).

---

## Fase 0 — Punto de partida

- [ ] La v2 corre y pasa su smoke test (tag `v2` presente).
- [ ] `git status` limpio.

**Verificar:** `curl http://localhost:8005/` → `"version":"v2"`.

## Fase 1 — El motor nuevo en el compose (sin tocar la API)

- [ ] `db/init_mariadb.sql`: la MISMA bdfacturas en dialecto MariaDB
      ([5_data_model.md](5_data_model.md)) — cópielo del proyecto del
      curso (es dato: mismas semillas o la regresión no será comparable).
- [ ] `docker-compose.yml`: servicio `mariadb` (11, puerto 13335, volumen
      `mariadbdata`, script montado, healthcheck).
- [ ] `docker compose up -d` — la API sigue en v2 contra PostgreSQL:
      **nada se rompe por agregar un contenedor**.

**Verificar:**
```powershell
docker compose exec mariadb mariadb -uroot -pparadigmas123 bdfacturas_mariadb_local -e "SHOW TABLES; SELECT COUNT(*) FROM producto;"   # 12 tablas · 8
```

## Fase 2 — Los repositorios MariaDB

- [ ] **aiomysql** en `requirements.txt` (+ `docker compose up -d --build`).
- [ ] Los 5 calcados (producto, persona, empresa, cliente, vendedor):
      misma clase con sufijo `MariaDB` y cadena `mysql+aiomysql://` — el
      SQL de los moldes NO cambia ([plan §2](3_plan.md)).
- [ ] `repositorio_factura_mariadb.py`: `CALL … @salida` + `SELECT
      @salida` en la misma transacción + traducción por código 1644 y
      patrón ([plan §4](3_plan.md)).

**Verificar:** la API arranca sin errores de import
(`docker compose logs api-facturas`). Nada los usa todavía.

## Fase 3 — La fábrica (ensamblador.py se reescribe)

- [ ] El diccionario `_FABRICAS` (proveedor → cadena + familia de
      repositorios) y `_crear_repositorio(entidad)` con el error claro.
- [ ] Las `crear_servicio_x()` conservan su firma y piden a la fábrica.
- [ ] `pruebas/prueba_capas.py`: criterio 5 (cada proveedor entrega SU
      dialecto con cadenas de mentira; DB_PROVIDER inválido → error claro).

**Verificar:** `docker compose exec api-facturas python
pruebas/prueba_capas.py` → todo OK.

## Fase 4 — El interruptor y el diagnóstico

- [ ] `docker-compose.yml`: `DB_MARIADB` + `DB_PROVIDER: ${DB_PROVIDER:-postgres}`.
- [ ] `main.py`: `version="v3"` + `motor` en el diagnóstico.

**Verificar:** `GET /` → `"motor":"postgres"` · con
`$env:DB_PROVIDER="mariadb"` y recrear la API → `"motor":"mariadb"`.

## Fase 5 — Verificación total y cierre

- [ ] **Regresión doble completa** ([7_quickstart.md](7_quickstart.md)
      §2): v1+v2 contra postgres → interruptor → v1+v2 contra mariadb.
- [ ] Errores de negocio idénticos en ambos motores (criterio 3).
- [ ] `git diff v2 --stat` respeta la frontera (criterio 4).
- [ ] Colección Postman: nota de la v3 (mismos endpoints, campo `motor`).
- [ ] Mapa y README actualizados · commit + tag `v3` + push.

**Verificar:** los 5 criterios de [2_spec.md](2_spec.md) §5 en verde.
