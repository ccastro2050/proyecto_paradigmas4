# Especificación — Versión 2: más tablas (los moldes y la factura)

> **Versión 2** del desarrollo incremental ([mapa de versiones](../0_mapa_versiones.md)).
> Rige la constitución: [../../1_constitution.md](../../1_constitution.md).
> **Acumulativa:** contiene TODO lo de la v1 — producto no se toca y su
> contrato sigue vigente tal cual.
>
> | Documento de esta versión | Contenido |
> |---|---|
> | **2_spec.md** (este) | QUÉ agrega la v2 y sus criterios de aceptación |
> | [3_plan.md](3_plan.md) | CÓMO: el molde replicado 4 veces y la factura vía SPs |
> | [4_research.md](4_research.md) | Decisiones y alternativas *(lectura opcional)* |
> | [5_data_model.md](5_data_model.md) | Las 5 tablas nuevas, sus semillas, el trigger y los SPs |
> | [6_contracts.md](6_contracts.md) | Los 28 endpoints nuevos con formatos exactos |
> | [7_quickstart.md](7_quickstart.md) | Regresión v1 y smoke test de la v2 |
> | [8_tasks.md](8_tasks.md) | Orden de construcción por fases verificables |

---

## 1. Propósito de la v2

Dos lecciones en una versión:

1. **El molde es industrial.** La rebanada de la v1 (modelos por verbo →
   controller → servicio → repositorio, cruzando por interfaces) se replica
   CUATRO veces: **persona, empresa, cliente y vendedor**. Réplicas casi
   mecánicas — esa facilidad ES la evidencia de que la arquitectura de la
   v1 estaba bien cortada.
2. **La API como traductora.** `factura` es maestro-detalle y su lógica ya
   VIVE en la BD (los SPs y el trigger de `db/init.sql`, ahí desde el día
   1): la API no calcula subtotales ni descuenta stock — llama
   procedimientos, traduce su JSON y sus errores. La transacción es de la
   BD (ACID en serio).

## 2. Alcance

**Incluye:** CRUD completo de persona, empresa, cliente y vendedor ·
factura maestro-detalle vía SPs (listar, consultar, crear, anular) · la
excepción de negocio de conflicto (→ 409) · diagnóstico pasa a
`"version": "v2"` · la prueba de capas crece con persona.

**No incluye (deliberado — [mapa](../0_mapa_versiones.md)):**
- **Otros motores ni fábrica** (v3: MariaDB y `DB_PROVIDER`): el
  ensamblador sigue siendo funciones simples — YAGNI con dirección.
- usuario, rol, ruta y las tablas puente (completan la BD en la v4).
- CRUD directo de `productosporfactura`: sus renglones se gestionan a
  través de factura.
- Borrado físico de facturas por la API: solo **anular** (borrado lógico).

## 3. Requisitos funcionales

### RF1 — Cuatro moldes más (persona, empresa, cliente, vendedor)
Los 6 endpoints del patrón v1 (listar `?limite`, obtener, POST, PUT,
PATCH, DELETE) sobre:

| Entidad | PK | Campos |
|---|---|---|
| `persona` | codigo (str 1-10) | nombre (≤100), email (≤100), telefono (≤20) |
| `empresa` | codigo (str 1-10) | nombre (≤100) |
| `cliente` | id (SERIAL) | credito (decimal ≥ 0, opcional al crear: default 0 en BD), fkcodpersona (req), fkcodempresa (opcional — puede ser null) |
| `vendedor` | id (SERIAL) | carnet (int ≥ 0), direccion (≤100), fkcodpersona (req) |

FK violada (fkcodpersona inexistente) → 500 con el error del motor en
`detalle` (la BD es la última defensa). La pareja didáctica PUT/PATCH
aplica en los cuatro.

### RF2 — Factura maestro-detalle (la API como traductora)

```
GET  /api/factura              → todas, con nombres resueltos y detalle adentro (SP listar)
GET  /api/factura/{numero}     → una, igual de completa (SP consultar) · 404 si no existe
POST /api/factura              → crea cabecera + renglones EN UNA transacción (SP insertar)
POST /api/factura/{numero}/anular → borrado LÓGICO: estado='anulada' + stock restaurado (SP anular)
```

- El body del POST: `{fkidcliente, fkidvendedor, productos: [{codigo,
  cantidad}, …]}` — **nadie envía subtotales ni total**: los calcula el
  trigger. Lista vacía → **422** (Pydantic la corta antes de la BD).
- Stock insuficiente (trigger) → **500** con el mensaje del motor.
- Anular dos veces → **409** · anular/consultar inexistente → **404**.

### RF3 — Diagnóstico
`GET /` → `"version": "v2"` (única alteración a lo existente).

## 4. Requisitos no funcionales

- **RNF1 — Los de la v1 siguen todos** (capas con interfaces Protocol,
  SQL parametrizado con text(), async, sobres de respuesta uniformes).
- **RNF2 — La traducción de excepciones crece una fila:** además de
  ValueError → 400 y LookupError → 404, nace `ConflictoError` → **409**
  (la factura ya estaba anulada). El controller sigue sin conocer al motor.
- **RNF3 — La API no calcula:** subtotal, total y stock los mueve la BD
  (trigger). Si un total no cuadra, se revisa la BD, no la API.
- **RNF4 — Sin anticipación:** nada de DB_PROVIDER, fábrica ni otros
  motores (v3).

## 5. Criterios de aceptación

1. **Regresión:** `docker compose up -d --build` y el smoke test COMPLETO
   de la [v1](../v1_producto_postgres/7_quickstart.md) §3 pasa tal cual
   (solo cambia `"version":"v2"`).
2. **Los moldes:** ciclo completo de los 5 verbos (con la pareja
   PUT/PATCH) para persona, empresa, cliente y vendedor. Cliente mínimo
   (solo `fkcodpersona`) queda con credito 0 y sin empresa; cliente con
   persona inexistente → 500 con FK.
3. **La cadena comercial:** crear empresa E100 → persona P010 → cliente
   (P010, E100) → vendedor (P010) → **factura con ESE cliente y ESE
   vendedor** → anularla. (Ojo: los ids autonuméricos se consumen también
   en los inserts fallidos — [4_research](4_research.md) D5.)
4. **Factura lee y escribe por SPs:** listar muestra las 6 semillas con
   nombres y productos adentro; consultar la 1; la 999 → 404. Crear una
   factura de 2 renglones: la respuesta trae subtotales y total
   CALCULADOS y el stock bajó exactamente lo facturado.
5. **Errores de negocio:** `productos: []` → 422 · cantidad 9999 → 500
   "Stock insuficiente…" · anular restaura el stock · segunda anulación →
   409 · anular la 999 → 404.
6. **Prueba de capas ampliada:** `python pruebas/prueba_capas.py`
   ejercita producto Y persona con repositorios falsos — sin PostgreSQL.

## 6. Definición de TERMINADA

Los 6 criterios pasan → commit + tag `v2` → recién entonces se especifica
la v3 (el segundo motor y la fábrica).

## 7. Clarificaciones

> **Qué es esta sección:** el registro de las ambigüedades detectadas ANTES
> de planear, con la respuesta que se acordó y su razón. Es **la compuerta
> 1** del método (ver [SDD_SPECKIT](../../../SDD_SPECKIT.md)): mientras
> quede un `[NECESITA ACLARACIÓN: …]` en los requisitos de arriba, esta
> versión no pasa a la planeación.
>
> Las entradas de abajo se reconstruyeron **al cerrar la versión**, a
> partir de las decisiones que sus propios contratos ya dejaban fijadas.
> De aquí en adelante esta sección se llena **en vivo**, antes del
> `3_plan.md` — que es como debe ser.

| # | La pregunta | La respuesta acordada, con su razón | Dónde quedó |
|---|---|---|---|
| C1 | El listado sin filas, ¿es un error o un resultado? | Un resultado: **204 sin cuerpo**. Vacío no es error. | RF de listar · contrato del `GET` |
| C2 | `?limite=0` o negativo, ¿422 o 400? | **400**: la FORMA del dato es correcta (sí es un entero); lo que se rompe es una regla de negocio. El 422 se reserva para el body mal formado. | Contrato del `GET` · convenciones |
| C3 | Crear con una llave que ya existe, ¿409 o 500? | **500**, con el error del motor en `detalle`: la llave la defiende la BD, no la API. Convertirlo en 409 sería lógica de negocio que esta versión no pide. | Convenciones de error · contrato del `POST` |
| C4 | `PATCH` con el body vacío, ¿200 sin hacer nada, o error? | **400**: pedir una actualización sin decir qué actualizar es una regla de negocio rota. | Contrato del `PATCH` |
| C5 | Una factura equivocada, ¿se borra o se anula? | Se **anula**: borrado lógico que restaura el stock. La factura es un hecho contable; borrarla perdería la trazabilidad. | RF de anulación · contrato de anular |
| C6 | Anular dos veces la misma factura, ¿qué responde? | **409**: el conflicto es de estado, no de forma ni de existencia. La factura existe (no es 404) y el body está bien (no es 422). | Contrato de anular |

**Cómo se escribe una entrada nueva:** la pregunta tal como se hizo (no
"revisar el borrado", sino "¿físico o lógico?"), la respuesta **con su
razón**, y el documento donde quedó plasmada. Si la respuesta cambia un
requisito, se corrige el requisito allá arriba: esta sección lo registra,
no lo reemplaza.
