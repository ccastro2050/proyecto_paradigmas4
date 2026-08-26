# Especificación — Versión 3: el segundo motor (MariaDB) y la fábrica

> **Versión 3** del desarrollo incremental ([mapa de versiones](../0_mapa_versiones.md)).
> Rige la constitución: [../../1_constitution.md](../../1_constitution.md).
> **Acumulativa:** contiene TODO lo de v1 y v2 — los 35 endpoints
> existentes no se tocan y sus contratos siguen vigentes tal cual.
>
> | Documento de esta versión | Contenido |
> |---|---|
> | **2_spec.md** (este) | QUÉ agrega la v3 y sus criterios de aceptación |
> | [3_plan.md](3_plan.md) | CÓMO: la fábrica, los 6 repositorios MariaDB y el interruptor |
> | [4_research.md](4_research.md) | Decisiones y alternativas *(lectura opcional)* |
> | [5_data_model.md](5_data_model.md) | La MISMA bdfacturas, ahora en dialecto MariaDB |
> | [6_contracts.md](6_contracts.md) | CERO endpoints nuevos — esa es la gracia |
> | [7_quickstart.md](7_quickstart.md) | La regresión DOBLE: todo pasa en ambos motores |
> | [8_tasks.md](8_tasks.md) | Orden de construcción por fases verificables |

---

## 1. Propósito de la v3

**Cobrar la promesa de las capas.** Desde la v1 el proyecto repite que
controllers y servicios "no saben qué motor hay debajo". La v3 lo somete
al examen: aparece un **segundo motor (MariaDB)** con la MISMA bdfacturas,
y la API entera — 35 endpoints, validaciones Pydantic, errores de negocio,
triggers y SPs — funciona idéntica contra cualquiera de los dos. **Sin
tocar UNA línea por encima de los repositorios.**

Y nace lo anunciado desde la v1: el ensamblador de funciones simples se
convierte en la **fábrica real** con `DB_PROVIDER` — UN punto del código
decide el motor; el resto pide interfaces.

## 2. Alcance

**Incluye:** servicio `mariadb` en el compose (misma BD semilla, mismos
ids) · los 6 repositorios en dialecto MariaDB · la fábrica en
`ensamblador.py` con el interruptor **`DB_PROVIDER`** (`postgres` |
`mariadb`, default postgres) · diagnóstico pasa a `"version": "v3"` y
estrena `"motor"` · la prueba de capas crece con la fábrica.

**No incluye (deliberado — [mapa](../0_mapa_versiones.md)):**
- **SQL Server** (v4): el tercer motor esperará — con la fábrica puesta,
  costará un bloque en el diccionario.
- Selección de motor por petición: descartada del curso. En v3 el motor
  se elige UNA vez, al arrancar.
- Cambios de contrato: ningún endpoint nuevo, ningún campo nuevo (salvo
  `motor` en el diagnóstico).

## 3. Requisitos funcionales

### RF1 — La fábrica de repositorios (nace en `ensamblador.py`)
- El ensamblador deja de conocer UNA clase por entidad y pasa a conocer
  **familias**: un diccionario `proveedor → {entidad → clase}`.
- Las funciones `crear_servicio_x()` NO cambian de firma: los controllers
  no se enteran de que ahora hay fábrica (esa es la mitad del examen).
- `DB_PROVIDER` inválido → error claro al primer uso, con los proveedores
  válidos en el mensaje.

### RF2 — El motor por configuración (el interruptor)
- Variable de entorno **`DB_PROVIDER`**: `postgres` (default) | `mariadb`.
- En Docker la fija el compose (`${DB_PROVIDER:-postgres}`): cambiar de
  motor es recrear SOLO el contenedor de la API — sin tocar código.
- Dos cadenas conviven en el entorno: `DB_POSTGRES` y `DB_MARIADB`.

### RF3 — El segundo motor completo
- Servicio `mariadb` (MariaDB 11) en el compose, puerto publicado
  **13335**, con `db/init_mariadb.sql`: las MISMAS 12 tablas, las MISMAS
  semillas (mismos ids, con `AUTO_INCREMENT` alineado), los triggers de
  totales/stock y los SPs de factura — en dialecto MariaDB
  ([5_data_model](5_data_model.md)).
- Los 6 `RepositorioXMariaDB` (aiomysql): mismos contratos, mismo SQL
  parametrizado (el dialecto de los moldes es idéntico — esa también es
  una lección).
- El de factura llama los SPs con `CALL … @salida` + `SELECT @salida`
  (el OUT de MariaDB) y traduce los `SIGNAL SQLSTATE '45000'` a las
  MISMAS excepciones de negocio: "no existe" → 404 · "ya está anulada" →
  409 · el resto (stock, mínimo) → 500.

### RF4 — Diagnóstico
`GET /` → `{mensaje, version: "v3", motor: "postgres"|"mariadb",
documentacion}`. El campo `motor` es la única adición visible.

## 4. Requisitos no funcionales

- **RNF1 — Los de v1 y v2 siguen todos** (capas con Protocol, SQL
  visible y parametrizado, async, sobres uniformes).
- **RNF2 — La frontera es el repositorio:** el diff de la v3 NO toca
  `controllers/`, `servicios/servicio_*.py`, `servicios/abstracciones/`
  ni `models/`. Si algo de ahí "necesitara" cambiar, la v3 está mal
  planteada.
- **RNF3 — Paridad de semillas:** ambos motores arrancan con datos
  idénticos — el smoke test es EL MISMO.
- **RNF4 — Sin anticipación:** nada de SQL Server (v4) ni motor por
  petición (v5).

## 5. Criterios de aceptación

1. **Regresión total contra PostgreSQL (motor por defecto):** `docker
   compose up -d --build` y los smoke tests COMPLETOS de
   [v1](../v1_producto_postgres/7_quickstart.md) §3 y
   [v2](../v2_mas_tablas/7_quickstart.md) §3 pasan tal cual (solo cambia
   el diagnóstico: `"version":"v3"`, `"motor":"postgres"`).
2. **El interruptor:** `DB_PROVIDER=mariadb` + recrear SOLO la API → el
   diagnóstico dice `"motor":"mariadb"` y la MISMA regresión total pasa
   contra MariaDB. Ni una línea de código cambió entre 1 y 2.
3. **Los errores de negocio son idénticos en ambos motores:** factura
   999 → 404 · doble anulación → 409 · stock insuficiente → 500 · FK/PK
   violadas → 500. (El `detalle` puede variar en redacción — el `estado`
   y el `mensaje` no.)
4. **El diff respeta la frontera:** `git diff v2 --stat` solo toca
   `repositorios/*mariadb*`, `servicios/ensamblador.py`, `main.py`,
   `requirements.txt`, `docker-compose.yml`, `db/init_mariadb.sql`,
   `pruebas/`, `postman/` y `docs/`.
5. **Prueba de capas ampliada:** la fábrica entrega el repositorio del
   dialecto pedido SIN abrir conexiones (construir no conecta) — y con
   `DB_PROVIDER` inválido falla con mensaje claro.

## 6. Definición de TERMINADA

Los 5 criterios pasan → commit + tag `v3` → la API es bi-motor → recién
entonces se especifica la v4 (SQL Server: la fábrica pagará de nuevo).
