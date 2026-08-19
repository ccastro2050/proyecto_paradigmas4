# Contratos HTTP — Versión 4: CERO endpoints nuevos (tercera vez, misma gracia)

> Los 35 endpoints de la [v1](../v1_producto_postgres/6_contracts.md) y la
> [v2](../v2_mas_tablas/6_contracts.md) siguen vigentes **tal cual, con
> LOS TRES motores**. La única línea que cambia:

```
GET /
→ 200 { "mensaje": "API Facturas funcionando", "version": "v4",
        "motor": "postgres" | "mariadb" | "sqlserver",
        "documentacion": "/docs" }
```

## Lo que el criterio 3 verifica, motor por motor

| Grupo | postgres | mariadb | sqlserver |
|---|---|---|---|
| producto (7) · moldes v2 (24) | idénticos | idénticos | idénticos (TOP en vez de LIMIT — invisible desde HTTP) |
| factura (4) | INOUT | OUT + @salida | OUTPUT + lote |
| 404 / 409 / 422 / 500 | idénticos | idénticos | idénticos |

**Matices honestos (igual que en la v3):** el `detalle` de los 500
redacta según el motor, y la serialización de decimales puede variar en
decimales visibles (5000000.0 vs 5000000.00) — el VALOR es contrato, el
formato del número no. Novedad del tercer motor: los mensajes de FK de
SQL Server llegan con prefijos ODBC en `detalle` — informativos, no
contractuales.
