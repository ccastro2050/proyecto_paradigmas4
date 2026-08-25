# Quickstart — API Facturas **v2**: los moldes y la factura

> **Versión 2** · Validación rápida de la v2 ya construida. Si aún no hay
> nada, empiece por [8_tasks.md](8_tasks.md).

---

## 1. Arrancar TODO (igual que en la v1)

```powershell
docker compose up -d --build
```

## 2. Regresión: la v1 sigue intacta (criterio 1)

Correr el smoke test COMPLETO de la
[v1](../v1_producto_postgres/7_quickstart.md) §3. Única diferencia
esperada: el diagnóstico dice `"version":"v2"`. Si algo de producto
cambió, la v2 está mal — las versiones son acumulativas.

## 3. Smoke test de lo nuevo (criterios 2 a 6)

```powershell
# ── 2. LOS MOLDES (aquí persona y cliente; repita el patrón con
#       empresa y vendedor) ──────────────────────────────────────────
curl http://localhost:8005/api/persona                       # 6 personas
curl http://localhost:8005/api/persona/P001                  # Ana Torres
curl -X POST http://localhost:8005/api/persona -H "Content-Type: application/json" `
     -d '{\"codigo\":\"P007\",\"nombre\":\"Prueba V2\",\"email\":\"p7@correo.com\",\"telefono\":\"3007777777\"}'
curl -i -X PUT   http://localhost:8005/api/persona/P007 -H "Content-Type: application/json" `
     -d '{\"telefono\":\"3008888888\"}'                      # 422: a PUT le faltan campos
curl -X PATCH http://localhost:8005/api/persona/P007 -H "Content-Type: application/json" `
     -d '{\"telefono\":\"3008888888\"}'                      # 200: PATCH acepta subconjunto
curl -X DELETE http://localhost:8005/api/persona/P007
curl -i -X DELETE http://localhost:8005/api/persona/P001     # 500: FK (P001 es cliente)

curl http://localhost:8005/api/cliente                       # 4 clientes (ids 1,2,3,5)
# cliente MÍNIMO: credito lo pone el DEFAULT de la BD, empresa queda null:
curl -X POST http://localhost:8005/api/cliente -H "Content-Type: application/json" `
     -d '{\"fkcodpersona\":\"P001\"}'
# la FK como última defensa:
curl -i -X POST http://localhost:8005/api/cliente -H "Content-Type: application/json" `
     -d '{\"fkcodpersona\":\"P999\"}'                        # 500 FK

# ── 3. LA CADENA COMERCIAL (criterio 3) ─────────────────────────────
curl -X POST http://localhost:8005/api/empresa -H "Content-Type: application/json" `
     -d '{\"codigo\":\"E100\",\"nombre\":\"Empresa Nueva S.A.\"}'
curl -X POST http://localhost:8005/api/persona -H "Content-Type: application/json" `
     -d '{\"codigo\":\"P010\",\"nombre\":\"Cliente Nuevo\",\"email\":\"cn@correo.com\",\"telefono\":\"3010101010\"}'
curl -X POST http://localhost:8005/api/cliente -H "Content-Type: application/json" `
     -d '{\"fkcodpersona\":\"P010\",\"fkcodempresa\":\"E100\",\"credito\":500000}'
curl http://localhost:8005/api/cliente     # ← ANOTE el id del cliente de P010 (los
#     autonuméricos se consumen también en los inserts fallidos — research D5)
curl -X POST http://localhost:8005/api/vendedor -H "Content-Type: application/json" `
     -d '{\"carnet\":1004,\"direccion\":\"Calle 9 #8-70\",\"fkcodpersona\":\"P010\"}'
curl http://localhost:8005/api/vendedor    # ← anote el id (será 4)
# la factura de la cadena (use LOS IDS ANOTADOS) y anúlela al final del smoke.

# ── 4. FACTURA LEE POR SPs (criterio 4) ─────────────────────────────
curl http://localhost:8005/api/factura                       # 6 con nombres y productos adentro
curl http://localhost:8005/api/factura/1                     # una completa
curl -i http://localhost:8005/api/factura/999                # 404

# El stock ANTES:
curl http://localhost:8005/api/producto/PR001                # stock 17
curl http://localhost:8005/api/producto/PR003                # stock 42
# Crear (2 renglones — nadie envía subtotales):
curl -X POST http://localhost:8005/api/factura -H "Content-Type: application/json" `
     -d '{\"fkidcliente\":1,\"fkidvendedor\":1,\"productos\":[{\"codigo\":\"PR001\",\"cantidad\":2},{\"codigo\":\"PR003\",\"cantidad\":3}]}'
# ← la respuesta trae subtotales y total CALCULADOS; anote el numero (será 7)
curl http://localhost:8005/api/producto/PR001                # stock 15
curl http://localhost:8005/api/producto/PR003                # stock 39

# ── 5. ERRORES DE NEGOCIO (criterio 5) ──────────────────────────────
curl -i -X POST http://localhost:8005/api/factura -H "Content-Type: application/json" `
     -d '{\"fkidcliente\":1,\"fkidvendedor\":1,\"productos\":[]}'          # 422 (Pydantic)
curl -i -X POST http://localhost:8005/api/factura -H "Content-Type: application/json" `
     -d '{\"fkidcliente\":1,\"fkidvendedor\":1,\"productos\":[{\"codigo\":\"PR001\",\"cantidad\":9999}]}'  # 500 stock
curl -X POST http://localhost:8005/api/factura/7/anular      # 200: restaura stock
curl http://localhost:8005/api/producto/PR001                # stock volvió a 17
curl -i -X POST http://localhost:8005/api/factura/7/anular   # 409 ya anulada
curl -i -X POST http://localhost:8005/api/factura/999/anular # 404
```

**6. Prueba de capas** (sin PostgreSQL):

```powershell
cd api_facturas
python pruebas\prueba_capas.py
# → … y también persona con su repositorio falso — termina "PRUEBA DE CAPAS OK"
```

> Para dejar la BD como al inicio: `docker compose down -v && docker
> compose up -d` (la factura 7 anulada NO se borra — así es el negocio).

## 4. Si algo falla

| Síntoma | Causa probable |
|---|---|
| Los de la v1 ([quickstart v1](../v1_producto_postgres/7_quickstart.md) §4) | Aplican igual |
| POST de factura 500 con FK | fkidcliente/fkidvendedor no existen — use los semilla (clientes 1,2,3,5 · vendedores 1,2,3) |
| GET /api/factura 500 "procedure … does not exist" | La BD es vieja: `docker compose down -v && up -d` re-crea con los SPs |
| El total no cuadra | No es la API (no calcula nada): revise el trigger en `db/init.sql` |
| Anular da 500 en vez de 409/404 | El repositorio no está traduciendo P0001 por patrón — [3_plan.md](3_plan.md) §3 |
