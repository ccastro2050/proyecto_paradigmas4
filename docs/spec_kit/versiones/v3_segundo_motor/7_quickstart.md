# Quickstart — API Facturas **v3**: arranque y la regresión DOBLE

> **Versión 3** · Validación rápida de la v3 ya construida. Si aún no hay
> nada, empiece por [8_tasks.md](8_tasks.md).

---

## 1. Arrancar TODO (ahora con dos motores)

```powershell
docker compose up -d --build
```

Quedan corriendo: `postgres` (healthy), **`mariadb` (healthy — también se
inicializa solo la primera vez)** y `api-facturas`.

## 2. La regresión doble (criterios 1 y 2 — el corazón de la v3)

### 2a. TODO contra PostgreSQL (el motor por defecto)

```powershell
curl http://localhost:8005/     # → "version":"v3", "motor":"postgres"
```

Correr COMPLETOS los smoke tests de la
[v1](../v1_producto_postgres/7_quickstart.md) §3 y la
[v2](../v2_mas_tablas/7_quickstart.md) §3. **Pasan tal cual** — mismos
ids, mismos stocks, mismos 404/409/422/500.

### 2b. El interruptor: los MISMOS tests contra MariaDB

```powershell
$env:DB_PROVIDER = "mariadb"
docker compose up -d api-facturas      # recrea SOLO la API (segundos)
curl http://localhost:8005/            # → "motor":"mariadb"
```

Correr la MISMA regresión completa. Pasa igual. **Eso** — ninguna línea
de código cambió entre 2a y 2b — es la demostración de que las capas
eran verdad.

> ⚠️ Cada motor guarda lo suyo: lo que usted creó en 2a vive solo en
> PostgreSQL. Para el estado semilla exacto:
> `docker compose down -v && docker compose up -d`.

Para volver al default (PostgreSQL):

```powershell
Remove-Item Env:DB_PROVIDER
docker compose up -d api-facturas
```

## 3. Los errores de negocio en el motor nuevo (criterio 3)

Con `motor=mariadb` (la regresión ya los cubre — aquí los tres
emblemáticos):

```powershell
curl -i http://localhost:8005/api/factura/999               # 404 "Factura 999 no existe"
curl -i -X POST http://localhost:8005/api/factura -H "Content-Type: application/json" `
     -d '{\"fkidcliente\":1,\"fkidvendedor\":1,\"productos\":[{\"codigo\":\"PR001\",\"cantidad\":9999}]}'  # 500 "Stock insuficiente…"
# (anule dos veces cualquier factura suya: la segunda → 409)
```

## 4. La frontera del diff (criterio 4)

```powershell
git diff v2 --stat
```

NADA de `controllers/`, `servicios/servicio_*.py`,
`servicios/abstracciones/` ni `models/` aparece. La v3 vive de los
repositorios hacia abajo (+ el ensamblador, que para eso existía).

## 5. La prueba de capas (criterio 5)

```powershell
docker compose exec api-facturas python pruebas/prueba_capas.py
# → … LA FÁBRICA OK: cada proveedor entrega su dialecto, sin abrir conexiones
```

## 6. Si algo falla

| Síntoma | Causa probable |
|---|---|
| Los de v1/v2 | Aplican todos igual (sus quickstarts) |
| `mariadb` no queda healthy | Puerto 13335 ocupado, o volumen de un intento fallido: `docker compose down -v` y de nuevo |
| Todo 500 con `motor=mariadb` | ¿`db/init_mariadb.sql` corrió? Solo se auto-ejecuta con el volumen VACÍO — `docker compose down -v && up -d` |
| `GET /` dice un motor y usted esperaba el otro | `DB_PROVIDER` quedó fijo en su PowerShell: `Remove-Item Env:DB_PROVIDER` y recree la API |
| "DB_PROVIDER inválido: …" en los logs | Valor mal escrito (solo `postgres` o `mariadb`) |
| Factura da 500 en vez de 404/409 en mariadb | El repositorio no está traduciendo el código 1644 + patrón — [3_plan.md](3_plan.md) §4 |
