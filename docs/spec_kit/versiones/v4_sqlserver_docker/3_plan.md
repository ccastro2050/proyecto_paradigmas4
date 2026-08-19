# Plan — Versión 4: el tercer motor (SQL Server) y el compose completo

> Cómo se construye lo especificado en [2_spec.md](2_spec.md).

---

## 1. Inventario de archivos

**Nuevos (8):**

```
db/bdfacturas_sqlserver.sql                      ← la MISMA bdfacturas, dialecto T-SQL
db/init_sqlserver.sh                             ← el inicializador (SQL Server no auto-ejecuta)
api_facturas/repositorios/repositorio_{producto,persona,empresa,cliente,
    vendedor,factura}_sqlserver.py               ← los 6 dialectos T-SQL
```

**Crecen:**

| Archivo | Qué crece |
|---|---|
| `docker-compose.yml` | ★ `sqlserver` (2022, :11432, healthcheck con sqlcmd) + `sqlserver-init` + `DB_SQLSERVER` y el tercer valor de `DB_PROVIDER` |
| `api_facturas/Dockerfile` | ★ el driver **ODBC 18** de Microsoft (msodbcsql18 + unixodbc) |
| `api_facturas/requirements.txt` | ★ **aioodbc** |
| `servicios/ensamblador.py` | ★ UN bloque `"sqlserver"` en `_FABRICAS` (+ imports) — la cuenta de la fábrica |
| `main.py` | ★ `version="v4"` |
| `pruebas/prueba_capas.py` | ★ el tercer dialecto en la prueba de la fábrica |

**Intocables (RNF2):** `controllers/`, `servicios/servicio_*.py`,
`servicios/abstracciones/`, `models/`, `excepciones.py`.

## 2. Los 5 moldes: la PRIMERA diferencia real de dialecto

En la v3 el SQL de los moldes resultó idéntico. En la v4 no del todo —
T-SQL no tiene `LIMIT`:

| PostgreSQL / MariaDB | SQL Server |
|---|---|
| `SELECT cols FROM t ORDER BY pk LIMIT :limite` | `SELECT TOP (:limite) cols FROM t ORDER BY pk` |
| todo lo demás (INSERT/UPDATE/DELETE, SET dinámico, :parámetros) | **idéntico** |

## 3. El repositorio de factura (tercer mecanismo de OUT)

| Motor | Cómo devuelve el SP su JSON |
|---|---|
| PostgreSQL | `INOUT` — el CALL lo devuelve como fila |
| MariaDB | `OUT` — `CALL …, @salida` y luego `SELECT @salida` |
| SQL Server | `OUTPUT` — un LOTE: `SET NOCOUNT ON; DECLARE @salida NVARCHAR(MAX); EXEC sp_x …, @p_resultado = @salida OUTPUT; SELECT @salida;` |

El `SET NOCOUNT ON` importa: sin él, cada INSERT interno del SP emite un
conteo de filas y el `SELECT @salida` deja de ser el primer resultado
del lote.

**Traducción de errores:** los `THROW 5000x` llegan por ODBC con el
mensaje envuelto en prefijos (`[42000] [Microsoft][ODBC Driver 18…]`);
el repositorio lo LIMPIA y aplica los MISMOS patrones de siempre
("no existe" → `LookupError` · "anulada" → `ConflictoError` · resto →
sube). Tres motores, tres señales (P0001, 1644, THROW), una frontera.

## 4. La imagen de la API crece (Dockerfile)

aioodbc habla ODBC y ODBC necesita el driver NATIVO de Microsoft:

```dockerfile
RUN apt-get update && apt-get install -y curl gnupg2 unixodbc \
 && curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft.gpg \
 && echo "deb [signed-by=…] https://packages.microsoft.com/debian/12/prod bookworm main" > /etc/apt/sources.list.d/mssql.list \
 && apt-get update && ACCEPT_EULA=Y apt-get install -y msodbcsql18
```

(asyncpg y aiomysql no pidieron nada — la asimetría de los ecosistemas
también es contenido del curso.)

La cadena lleva el driver y la confianza del certificado:

```
mssql+aioodbc://sa:Paradigmas123!@sqlserver:1433/bdfacturas_sqlserver_local
    ?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes
```

## 5. El compose queda completo (infraestructura de datos)

- `sqlserver` con healthcheck REAL (sqlcmd `SELECT 1`, `start_period:
  30s` porque el motor tarda) y `sqlserver-init` que corre el script UNA
  vez — el contraste con los otros dos motores que se inicializan solos.
- La API espera: `postgres` healthy + `mariadb` healthy +
  `sqlserver-init` completed_successfully.
- Puertos publicados: 8002 (API) · 15432 (postgres) · 13332 (mariadb) ·
  **11432 (sqlserver)**. Reconstrucción del estudiante: +100.
