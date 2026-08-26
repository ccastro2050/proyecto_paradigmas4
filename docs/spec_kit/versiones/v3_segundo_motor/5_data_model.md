# Modelo de datos — Versión 3: la MISMA bdfacturas, en MariaDB

> La v3 no agrega ni una tabla ni una columna: agrega un DIALECTO.
> `db/init_mariadb.sql` crea en MariaDB la misma base que `db/init.sql`
> crea en PostgreSQL: 12 tablas, triggers de totales/stock, SPs de
> factura y las mismas semillas (mismos ids). La BD se llama
> `bdfacturas_mariadb_local`. El script es idéntico al del proyecto
> gemelo PHP del curso — misma BD, otra API.

---

## 1. Equivalencias de dialecto (lo que cambia al portar el DDL)

| Concepto | PostgreSQL | MariaDB |
|---|---|---|
| Autonumérico | `SERIAL` | `INT AUTO_INCREMENT` |
| Alinear secuencia tras ids explícitos | `setval('t_id_seq', MAX)` | `ALTER TABLE t AUTO_INCREMENT = n` |
| Decimal | `NUMERIC` | `DECIMAL(18,2)` |
| Error de negocio | `RAISE EXCEPTION '…'` (SQLSTATE `P0001`) | `SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = …` (código **1644**) |
| SP con salida | `INOUT p_resultado JSON` (el CALL la devuelve como fila) | `OUT p_resultado JSON` (se recoge con `SELECT @salida`) |
| Abrir JSON de entrada | `json_array_elements()` | `JSON_EXTRACT()` + `WHILE` (no hay FOR sobre arrays) |
| Armar JSON de salida | `json_build_object` / `json_agg` | `JSON_OBJECT` / `GROUP_CONCAT` + `CONCAT` |
| El trigger | UNA función `BEFORE INSERT OR UPDATE OR DELETE` | SEIS triggers (BEFORE/AFTER × INSERT/UPDATE/DELETE — MariaDB no permite OR ni tocar la misma tabla en un solo trigger) |
| Tipo JSON | tipo real | alias de `LONGTEXT` (por eso el JSON de entrada viaja como texto sin cast) |

Las 12 tablas, sus PKs, FKs, el `UNIQUE(ruta)`, el DEFAULT de `credito`,
el `ON DELETE CASCADE` de `productosporfactura` — **idénticos** en
estructura y nombre.

## 2. Los mismos actores, tercer acento

- **Los triggers** (`trg_prodfact_*`): mismos papeles que el trigger de
  PostgreSQL — validar stock, calcular `subtotal`, descontar/restaurar
  `stock`, recalcular `total` — repartidos en 6 por las reglas de MariaDB.
- **Los SPs de factura** conservan NOMBRE y semántica:
  `sp_insertar_factura_y_productosporfactura`, `sp_consultar…`,
  `sp_listar…` (nombres de cliente/vendedor resueltos, detalle adentro),
  `sp_actualizar…`, `sp_borrar…` y `sp_anular_factura`.
- **Los mensajes que la API traduce** son idénticos a los de PostgreSQL:
  `Factura N no existe` → 404 · `Factura N ya está anulada` → 409 ·
  `Stock insuficiente…` → 500. (Por eso el repositorio MariaDB reutiliza
  los MISMOS patrones de texto.)
- Los SPs de usuarios/roles/permisos también viajan en el script: la v3
  no los llama, pero mantienen la paridad con el gemelo — quedarán para el login
  del front (v5).

## 3. Semillas (idénticas a PostgreSQL — RNF3)

| Tabla | Filas | Igual que en PostgreSQL |
|---|---|---|
| producto | 8 | PR001 stock 17 · PR003 stock 42 (los números de la regresión) |
| persona | 6 | P001 Ana Torres … P006 |
| empresa | 3 | E001, E002, E999 |
| cliente | 4 | ids **1, 2, 3, 5** (AUTO_INCREMENT queda en 6) |
| vendedor | 3 | ids 1-3, carnets 1001-1003 (AUTO_INCREMENT en 4) |
| factura | 6 | numeros 1-6 con sus 12 renglones (AUTO_INCREMENT en 7) |
| rol · ruta · usuario · puentes | 5 · 15 · 8 · 21+25 | mismas filas (las usará la v4/v5) |

Detalle del script: las facturas semilla se insertan con los triggers
TEMPORALMENTE eliminados (MariaDB no tiene `DISABLE TRIGGER`) porque los
stocks semilla ya vienen descontados — y se recrean idénticos después.
