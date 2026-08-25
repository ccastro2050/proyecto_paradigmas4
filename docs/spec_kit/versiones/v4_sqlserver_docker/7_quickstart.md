# Quickstart — API Facturas **v4**: arranque y la regresión TRIPLE

> **Versión 4** · Validación rápida de la v4 ya construida. Si aún no hay
> nada, empiece por [8_tasks.md](8_tasks.md).

---

## 1. Arrancar TODO (ahora con tres motores)

```powershell
docker compose up -d --build
```

La primera vez tarda: la imagen de la API instala el driver ODBC y SQL
Server pide su tiempo. Al final: `postgres` (healthy), `mariadb`
(healthy), `sqlserver` (healthy), **`sqlserver-init` (Exited 0 — hizo su
trabajo y murió)** y `api-facturas` arriba.

> ⚠️ SQL Server necesita ~2 GB de RAM libres en Docker Desktop.

## 2. La regresión TRIPLE (criterios 1-3 — el corazón de la v4)

```powershell
curl http://localhost:8005/     # → "version":"v4", "motor":"postgres"
# → smoke tests COMPLETOS de v1 §3 y v2 §3: pasan tal cual

$env:DB_PROVIDER = "mariadb"
docker compose up -d api-facturas
curl http://localhost:8005/     # → "motor":"mariadb"
# → la MISMA regresión completa: pasa igual
# (para el estado semilla exacto entre motores: docker compose down -v && up -d)

$env:DB_PROVIDER = "sqlserver"
docker compose up -d api-facturas
curl http://localhost:8005/     # → "motor":"sqlserver"
# → la MISMA regresión completa, tercera vez. Ni una línea de código
#   cambió entre las tres pasadas: ESO es Liskov entre repositorios.

Remove-Item Env:DB_PROVIDER            # volver al default (postgres)
docker compose up -d api-facturas
```

## 3. La frontera del diff (criterio 4)

```powershell
git diff v3 --stat
```

NADA de `controllers/`, `servicios/servicio_*.py`,
`servicios/abstracciones/` ni `models/`. Y en `ensamblador.py` el diff
es UN bloque en `_FABRICAS` + imports — la cuenta de la fábrica, pagada.

## 4. La prueba de capas (criterio 5)

```powershell
docker compose exec api-facturas python pruebas/prueba_capas.py
# → … LA FÁBRICA OK: cada proveedor entrega su dialecto, sin abrir conexiones
```

## 5. Si algo falla

| Síntoma | Causa probable |
|---|---|
| Los de v1/v2/v3 | Aplican todos igual |
| `sqlserver` nunca queda healthy | Le falta RAM (~2 GB) o el disco de Docker está lleno |
| `sqlserver-init` Exited(1) | La clave de `sa` no coincide o el motor no estaba sano: `docker compose logs sqlserver-init` |
| Todo 500 con `motor=sqlserver` | ¿El init corrió? `docker compose logs sqlserver-init` debe decir "inicializado correctamente" |
| "Can't open lib 'ODBC Driver 18…'" | La imagen vieja no tiene el driver: `docker compose up -d --build` (reconstruye con el Dockerfile de la v4) |
| Factura da 500 en vez de 404/409 en sqlserver | La traducción por patrón no está limpiando el prefijo ODBC — [3_plan.md](3_plan.md) §3 |
| RAM justa | `docker compose stop sqlserver sqlserver-init` libera el motor pesado mientras trabaja con los otros |
