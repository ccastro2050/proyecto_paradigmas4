# Modelo de datos — Versión 4: la MISMA bdfacturas, en SQL Server

> Tercera y última copia del dato: `db/bdfacturas_sqlserver.sql` crea en
> SQL Server la misma base que ya vive en PostgreSQL y MariaDB — 12
> tablas, triggers, SPs de factura y semillas idénticas. La BD se llama
> `bdfacturas_sqlserver_local`. El script es idéntico al del proyecto
> gemelo del curso (C# + SQL Server).

---

## 1. Equivalencias de dialecto (tercera columna de la tabla mental)

| Concepto | PostgreSQL | MariaDB | SQL Server |
|---|---|---|---|
| Autonumérico | `SERIAL` | `AUTO_INCREMENT` | `INT IDENTITY(1,1)` |
| Ids explícitos en semillas | `setval()` | `ALTER TABLE … AUTO_INCREMENT` | `SET IDENTITY_INSERT t ON/OFF` |
| Texto | `VARCHAR` | `VARCHAR utf8mb4` | `NVARCHAR` |
| Error de negocio | `RAISE EXCEPTION` (P0001) | `SIGNAL 45000` (1644) | `THROW 5000x, 'msj', 1` |
| SP con salida | `INOUT` (fila del CALL) | `OUT` + `SELECT @salida` | `OUTPUT` + lote DECLARE/EXEC/SELECT |
| Abrir JSON de entrada | `json_array_elements` | `JSON_EXTRACT` + WHILE | **`OPENJSON`** |
| Armar JSON de salida | `json_build_object/agg` | `JSON_OBJECT` + CONCAT | **`FOR JSON PATH`** |
| Top-N | `LIMIT :n` | `LIMIT :n` | **`TOP (:n)`** |
| Auto-ejecuta scripts montados | sí | sí | **NO** (nace sqlserver-init) |

## 2. Los mismos actores, tercer acento

- **Triggers** (`trg_prodfact_insert/update/delete`): mismos papeles —
  validar stock (THROW 50001), calcular subtotal, mover stock, recalcular
  total.
- **SPs de factura**: mismos nombres, mismos papeles. Los THROW que la
  API traduce: **50003** (consultar: no existe) y **50010** (anular: no
  existe / ya está anulada) — con los MISMOS textos que los otros
  motores, así que la traducción por patrón es uniforme.
- Los SPs de usuarios/roles/permisos también están (paridad con el
  gemelo C# — terreno de la v5).

## 3. Semillas (idénticas — RNF3, por tercera vez)

| Tabla | Filas | Los números de la regresión |
|---|---|---|
| producto | 8 | PR001 stock 17 · PR003 stock 42 |
| persona · empresa | 6 · 3 | P001 Ana Torres · E001/E002/E999 |
| cliente · vendedor | 4 (ids 1,2,3,5) · 3 | IDENTITY queda en 6 y 4 |
| factura | 6 (+12 renglones) | IDENTITY queda en 7 |
| rol · ruta · usuario · puentes | 5 · 15 · 8 · 21+25 | las usará la v5 |

Nota del dialecto: en SQL Server los IDENTITY también se consumen en
inserts fallidos — la nota de la v2 sobre "anote el id, no lo suponga"
aplica en los tres motores por tres mecanismos distintos.
