# Especificación — Versión 4: el tercer motor (SQL Server) y el compose completo

> **Versión 4** del desarrollo incremental ([mapa de versiones](../0_mapa_versiones.md)).
> Rige la constitución: [../../1_constitution.md](../../1_constitution.md).
> **Acumulativa:** contiene TODO lo de v1 a v3 — los 35 endpoints
> existentes no se tocan y sus contratos siguen vigentes tal cual.
>
> | Documento de esta versión | Contenido |
> |---|---|
> | **2_spec.md** (este) | QUÉ agrega la v4 y sus criterios de aceptación |
> | [3_plan.md](3_plan.md) | CÓMO: el bloque nuevo de la fábrica y el dialecto T-SQL |
> | [4_research.md](4_research.md) | Decisiones y alternativas *(lectura opcional)* |
> | [5_data_model.md](5_data_model.md) | La MISMA bdfacturas, ahora en dialecto SQL Server |
> | [6_contracts.md](6_contracts.md) | CERO endpoints nuevos — tercera vez, misma gracia |
> | [7_quickstart.md](7_quickstart.md) | La regresión TRIPLE: todo pasa en los tres motores |
> | [8_tasks.md](8_tasks.md) | Orden de construcción por fases verificables |

---

## 1. Propósito de la v4

**Liskov a escala industrial, y la factura de la fábrica en cero.** La v3
demostró que un segundo motor entra sin tocar nada por encima de los
repositorios. La v4 sube la apuesta con el motor MÁS distinto de los
tres — SQL Server: otro protocolo (ODBC), otro dialecto (T-SQL con `TOP`
en vez de `LIMIT`), otra forma de entregar los OUT y hasta otro ritual de
arranque (no auto-ejecuta scripts: nace `sqlserver-init`). Y aun así:
**los tres repositorios de cada entidad son indistinguibles desde el
servicio** — eso ES la sustitución de Liskov, medida en verificaciones.

La segunda mitad del propósito: comprobar la cuenta de la fábrica.
Agregar el tercer motor debe costar **un bloque en `_FABRICAS`** (+ sus
archivos de dialecto). Ni un `if` nuevo, ni una línea arriba.

Con esto el compose queda COMPLETO en infraestructura de datos: las 12
tablas de bdfacturas viven idénticas en LOS TRES motores — el terreno
que pisará la API genérica (v5).

## 2. Alcance

**Incluye:** servicios `sqlserver` + `sqlserver-init` en el compose ·
`db/bdfacturas_sqlserver.sql` e `init_sqlserver.sh` · los 6
`RepositorioXSqlServer` (aioodbc + driver ODBC 18 en la imagen) · el
bloque `"sqlserver"` en la fábrica (`DB_PROVIDER` acepta el tercer
valor) · diagnóstico pasa a `"version": "v4"` · la prueba de capas crece
con el tercer dialecto.

**No incluye (deliberado):**
- Endpoints para usuario, rol, ruta o las tablas puente: esas tablas
  viven completas en los TRES motores desde el día 1, y su acceso llega
  con la **API genérica (v5)** — `/api/{tabla}` las cubrirá todas sin
  escribir 15 repositorios más. (Por eso esta API por-entidad se queda
  en sus 6 entidades: el contraste es la lección de la v5.)
- El front (v6). Cambios de contrato: ninguno.

## 3. Requisitos funcionales

### RF1 — El tercer motor completo
- `sqlserver` (2022, ~2 GB de RAM) publicado en **11435**, con
  healthcheck real (sqlcmd) y `start_period` de gracia.
- **`sqlserver-init`**: el contraste didáctico — SQL Server NO ejecuta
  scripts montados; este contenedor corre `db/bdfacturas_sqlserver.sql`
  UNA vez (idempotente) y muere con Exited(0).
- La BD: las MISMAS 12 tablas y semillas (mismos ids, vía
  `IDENTITY_INSERT`), triggers de totales/stock y SPs de factura — en
  T-SQL ([5_data_model](5_data_model.md)).

### RF2 — La fábrica acepta el tercer valor
- `DB_PROVIDER`: `postgres` (default) | `mariadb` | `sqlserver`.
- El costo de agregarlo queda a la vista en el diff: UN bloque en
  `_FABRICAS` + imports. Las `crear_servicio_x()` no cambian.

### RF3 — Los 6 repositorios SQL Server
- Moldes: mismo SQL salvo **`TOP (:limite)`** en vez de `LIMIT :limite`
  (la primera diferencia real de dialecto en los moldes — T-SQL).
- Factura: lote `SET NOCOUNT ON; DECLARE @salida …; EXEC sp_x …,
  @p_resultado = @salida OUTPUT; SELECT @salida;` y traducción de los
  THROW por patrón del mensaje (mismos textos: "no existe" → 404 ·
  "ya está anulada" → 409 · stock/FK → 500).
- La imagen de la API instala el **driver ODBC 18** de Microsoft
  (aioodbc lo necesita — Dockerfile).

### RF4 — Diagnóstico
`GET /` → `"version": "v4"` con el `motor` de siempre (ahora puede decir
`sqlserver`).

## 4. Requisitos no funcionales

- **RNF1 — Los de v1 a v3 siguen todos.**
- **RNF2 — La frontera es el repositorio:** el diff de la v4 NO toca
  `controllers/`, `servicios/servicio_*.py`, `servicios/abstracciones/`
  ni `models/`.
- **RNF3 — Paridad de semillas en LOS TRES motores:** el smoke test es
  EL MISMO, tres veces.
- **RNF4 — Sin anticipación:** nada de API genérica (v5) ni front (v6).

## 5. Criterios de aceptación

1. **Regresión total contra PostgreSQL** (motor por defecto): smoke
   tests completos de v1+v2 pasan tal cual (`"version":"v4"`,
   `"motor":"postgres"`).
2. **Regresión total contra MariaDB** (`DB_PROVIDER=mariadb`): idéntica.
3. **Regresión total contra SQL Server** (`DB_PROVIDER=sqlserver`):
   idéntica — mismos ids, mismos stocks, mismos 404/409/422/500. La
   TRIPLE regresión sin recompilar es el criterio estrella.
4. **El diff respeta la frontera y la cuenta de la fábrica:** `git diff
   v3 --stat` solo toca `repositorios/*sqlserver*`, `ensamblador.py`,
   `main.py`, `requirements.txt`, `Dockerfile`, `docker-compose.yml`,
   `db/`, `pruebas/`, `postman/` y `docs/`.
5. **Prueba de capas ampliada:** la fábrica entrega el dialecto
   SqlServer sin abrir conexiones, y el proveedor inválido sigue
   fallando claro.

## 6. Definición de TERMINADA

Los 5 criterios pasan → commit + tag `v4` → la API es tri-motor y la
infraestructura de datos está completa → recién entonces se especifica
la v5 (la API genérica: `/api/{tabla}` sobre cualquiera de los tres).
