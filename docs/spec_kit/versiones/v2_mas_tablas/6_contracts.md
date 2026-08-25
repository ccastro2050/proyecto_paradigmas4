# Contratos HTTP — Versión 2: los moldes y la factura

> **Versión 2** · Base: `http://localhost:8005`. Los 7 endpoints de la
> [v1](../v1_producto_postgres/6_contracts.md) siguen vigentes TAL CUAL
> (solo el diagnóstico dice `"version": "v2"`). Las convenciones (verbos,
> vías de envío, sobre de error en `detail`) son las mismas de la v1 §0.

---

## 0. Resumen de lo nuevo (28 endpoints)

| Entidad | Endpoints | Patrón |
|---|---|---|
| persona | 6 | el molde de la v1, PK string (`/{codigo}`) |
| empresa | 6 | ídem |
| cliente | 6 | el molde con PK **SERIAL** (`/{id_cliente}` entero) y opcionales |
| vendedor | 6 | el molde con PK SERIAL (`/{id_vendedor}` entero) |
| factura | 4 | maestro-detalle vía SPs (sin PUT/PATCH/DELETE — se ANULA) |

Traducción de errores (crece una fila — lo demás igual que v1):

| Origen | HTTP |
|---|---|
| Body inválido (Pydantic) | 422 |
| `ValueError` del servicio | 400 |
| `LookupError` | 404 |
| **`ConflictoError` (factura ya anulada)** | **409** |
| Error del motor (PK/FK, stock del trigger, BD caída) | 500 |

## 1. Los moldes (se muestran una vez; los cuatro son el mismo patrón)

### persona (PK string — igual para empresa, con solo `nombre`)

```
GET    /api/persona?limite=N   → 200 {tabla, limite, total, datos:[{codigo,nombre,email,telefono},…]} · 204 vacía · 400 limite ≤ 0
GET    /api/persona/P001       → 200 {codigo,nombre,email,telefono} · 404
POST   /api/persona            body {codigo,nombre,email,telefono} (todos) → 200 {estado,mensaje} · 422 · 500 PK duplicada
PUT    /api/persona/P001       body {nombre,email,telefono} (TODOS) → 200 {…,filasAfectadas} · 422 si falta uno · 404
PATCH  /api/persona/P001       body con un subconjunto → 200 · 400 body vacío · 404
DELETE /api/persona/P001       → 200 {…,filasEliminadas} · 404 · 500 si tiene cliente/vendedor (FK)
```

### cliente (PK SERIAL y opcionales — vendedor es igual con carnet/direccion)

```
GET    /api/cliente            → 200 {…, datos:[{id,credito,fkcodpersona,fkcodempresa},…]}  (fkcodempresa puede venir null)
GET    /api/cliente/3          → 200 · 404 (el 4 no existe en la semilla) · 422 si el id no es entero
POST   /api/cliente            body {fkcodpersona}                       → 200 (credito lo pone el DEFAULT de la BD; empresa queda null)
                               body {fkcodpersona,fkcodempresa,credito}  → 200 (completo)
                               body {fkcodpersona:"P999"}                → 500 (FK: la última defensa es de la BD)
PUT    /api/cliente/6          body {credito,fkcodpersona,fkcodempresa|null} (reemplazo completo) → 200 · 422 · 404
PATCH  /api/cliente/6          body {credito} → 200 · 400 vacío · 404
DELETE /api/cliente/6          → 200 · 404 · 500 si tiene facturas (FK)
```

## 2. Factura (la API como traductora — 4 endpoints, sin PUT/PATCH/DELETE)

### `GET /api/factura` — listar (SP listar)

```
→ 200 { "tabla": "factura", "total": 6, "datos": [
         { "numero": 1, "fecha": "…", "total": 5000000.0, "estado": "activa",
           "fkidcliente": 1, "nombre_cliente": "Ana Torres",
           "fkidvendedor": 1, "nombre_vendedor": "Carlos Pérez",
           "productos": [ { "codigo_producto": "PR001", "nombre_producto": "…",
                            "cantidad": 2, "valorunitario": 2500000.0,
                            "subtotal": 5000000.0 } ] }, … ] }
```

Los nombres resueltos y el detalle adentro los armó el SP — la API no hizo
ni un JOIN.

### `GET /api/factura/{numero}` — consultar (SP consultar)

```
GET /api/factura/1   → 200 (la misma forma de arriba, UNA factura)
GET /api/factura/999 → 404 detail {estado:404, mensaje:"Factura no encontrada.",
                                   detalle:"Factura 999 no existe"}
```

### `POST /api/factura` — crear (SP insertar + trigger)

Body (modelo `FacturaCrear`) — nadie envía subtotales ni total:

```
body { "fkidcliente": 1, "fkidvendedor": 1,
       "productos": [ { "codigo": "PR001", "cantidad": 2 },
                      { "codigo": "PR003", "cantidad": 3 } ] }
→ 200 { "estado": 200, "mensaje": "Factura creada exitosamente.",
        "factura": { "numero": 7, "fecha": "…", "total": 5450000.0,
                     "estado": "activa", … },
        "productos": [ …con subtotales CALCULADOS por el trigger… ] }
→ 422 productos: []  (Pydantic corta antes de la BD)
→ 500 "Stock insuficiente para producto …" (el trigger; nada quedó a medias)
→ 500 FK si el cliente/vendedor no existen
```

### `POST /api/factura/{numero}/anular` — borrado lógico (SP anular)

```
→ 200 { "estado": 200, "mensaje": "Factura anulada exitosamente.",
        "resultado": { "numero_anulado": 7, "total_anulado": 5450000.0,
                       "productos_afectados": 2, "estado": "anulada" } }
→ 409 detail {estado:409, mensaje:"La factura ya está anulada.", detalle:"Factura 7 ya está anulada"}
→ 404 si no existe
```

## 3. `GET /` — Diagnóstico

```
→ 200 { "mensaje": "API Facturas funcionando", "version": "v2",
        "documentacion": "/docs" }
```

## 4. Estabilidad de este contrato

Los 35 endpoints (7 de v1 + 28 de v2) no cambian en las versiones
siguientes: la v3 cambia el MOTOR por configuración con estos mismos
contratos — esa será la prueba de que las capas eran verdad.
