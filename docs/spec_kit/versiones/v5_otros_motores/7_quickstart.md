# Quickstart — Versión 5: arranque y la regresión DOBLE

> **Versión 5** · Validación rápida de la versión ya construida. Si aún no
> hay nada construido, empiece por [8_tasks.md](8_tasks.md).

---

## 1. Arrancar TODO (ahora con 4 servicios)

```powershell
docker compose up -d --build
```

La primera vez tarda: MariaDB pide su tiempo. Al final: `postgres`
(healthy — se siembra solo, como siempre), `mariadb` (healthy),
**`mariadb-init` (Exited 0 — hizo su trabajo y murió: la lección del
inicializador, prometida desde la v1)** y `api-facturas` arriba.

> ⚠️ MariaDB necesita ~2 GB de RAM libres en Docker Desktop.

## 2. La regresión doble (criterios 1 y 2 — el corazón de la v5)

### 2a. TODO contra PostgreSQL (el motor por defecto)

```powershell
curl.exe http://localhost:8005/     # → "version":"v5", "motor":"postgres"
```

Correr COMPLETOS los smoke tests de la
[v1](../v1_sin_fk/7_quickstart.md) §2, la
[v2](../v2_con_fk/7_quickstart.md) §3 y la
[v3](../v3_control_acceso/7_quickstart.md) §3. **Pasan tal cual.**

### 2b. El interruptor: los MISMOS tests contra MariaDB

```powershell
$env:DB_PROVIDER = "mariadb"
docker compose up -d api-facturas       # recrea SOLO la API (segundos)
curl.exe http://localhost:8005/         # → "motor":"mariadb"
```

Correr la MISMA regresión completa. Pasa igual — mismos ids, mismos
stocks, mismos 404/409/422/500. **Eso** — ninguna línea de código cambió
entre 2a y 2b — es la demostración de que las capas eran verdad.

> ⚠️ Cada motor guarda lo suyo: lo que usted creó en 2a vive solo en
> PostgreSQL. Para el estado semilla exacto:
> `docker compose down -v && docker compose up -d`.

Para volver al default (PostgreSQL):

```powershell
Remove-Item Env:DB_PROVIDER
docker compose up -d api-facturas
```

## 3. Los errores de negocio en el motor nuevo (criterio 3)

```powershell
curl.exe -i http://localhost:8005/api/factura/999                 # → 404 (THROW 50003 traducido)
curl.exe -i -X POST http://localhost:8005/api/factura -H "Content-Type: application/json" -d "{\"fkidcliente\":1,\"fkidvendedor\":1,\"productos\":[{\"codigo\":\"PR001\",\"cantidad\":9999}]}"   # → 500 "Stock insuficiente…"
# (anule dos veces cualquier factura suya: la segunda → 409, THROW 50010)
```

## 4. La frontera del diff (criterio 4)

```powershell
git diff v3 --stat
```

NADA de `controllers/`, `servicios/`, `models/`, `models/` ni
`excepciones.py` aparece en la lista. La v5 vive de repositorios hacia
abajo (+ el ensamblador, que para eso existe).

## 5. La prueba de capas (criterio 5)

```powershell
docker compose exec api-facturas uvicorn main:app --reload --project pruebas
# → … CRITERIO 5 OK: cada fábrica entrega los repositorios de su motor, sin abrir conexiones
```

## 6. Si algo falla

| Síntoma | Causa probable |
|---|---|
| Los de v1/v2/v3 | Aplican todos igual (sus quickstarts) |
| `mariadb` nunca queda healthy | Le falta RAM (~2 GB) o el disco de Docker está lleno |
| `mariadb-init` en Exited (1) | La clave de `sa` no coincide o el motor no estaba sano — `docker compose logs mariadb-init` |
| Todo 500 con `motor=mariadb` | ¿El init corrió? `docker compose logs mariadb-init` debe decir "inicializado correctamente" |
| `GET /` dice un motor y usted esperaba el otro | La variable `DB_PROVIDER` quedó fija en su PowerShell: `Remove-Item Env:DB_PROVIDER` y recree la API |
| "Motor desconocido: …" en los logs | Valor inválido en `DB_PROVIDER` (solo `postgres` o `mariadb`) |
| Factura da 500 en vez de 404/409 en mariadb | El repositorio no está filtrando por número + patrón — ver [3_plan.md](3_plan.md) §3 |
| RAM justa | `docker compose stop mariadb mariadb-init` libera el motor pesado mientras trabaja con postgres |
