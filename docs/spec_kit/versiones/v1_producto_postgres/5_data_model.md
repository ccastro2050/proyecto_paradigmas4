# Modelo de datos — Versión 1: la BD completa, la API solo usa `producto`

> **Versión 1** · Decisión clave: **la base de datos `bdfacturas` se crea
> COMPLETA desde el inicio** (las 12 tablas, sus datos de ejemplo, el trigger
> de totales/stock y los procedimientos almacenados). Usted ya vio bases de
> datos — la BD no es lo que se construye por versiones: **lo que crece
> versión a versión es la API**. La v1 solo usa la tabla `producto`; el resto
> ya está ahí, esperando a las versiones siguientes.

---

## 1. El script de la BD (artefacto de esta versión)

El script completo viene **provisto** en el repositorio: **`db/init.sql`**
(~960 líneas: 12 tablas, restricciones, secuencias, datos de ejemplo, trigger
y SPs en dialecto PostgreSQL). **Se copia tal cual — no se escribe ni se
genera con IA.** Es infraestructura dada, igual que la imagen de PostgreSQL.

Vista rápida de lo que crea:

```
Independientes:  empresa · persona · producto · rol · ruta · usuario
Con FK:          cliente · vendedor · factura · productosporfactura
                 rol_usuario · rutarol
Lógica en BD:    trigger actualizar_totales_y_stock (productosporfactura)
                 + procedimientos almacenados de facturación y RBAC
```

## 2. La tabla que la v1 SÍ usa: `producto`

| Columna | Tipo | Restricción | Descripción |
|---|---|---|---|
| `codigo` | VARCHAR(10) | **PK** | Identificador legible (PR001…) |
| `nombre` | VARCHAR(100) | NOT NULL | Nombre del producto |
| `stock` | INTEGER | NOT NULL | Unidades disponibles |
| `valorunitario` | NUMERIC | NOT NULL | Precio unitario |

Datos de ejemplo: **8 productos** (PR001 Laptop Lenovo IdeaPad, 17,
2.500.000 … PR008 Disco Duro Seagate 1TB, 32, 280.000).

**Nota sobre validación:** los valores no-negativos de stock y valorunitario
los garantiza **Pydantic en la API** (la frontera de entrada, con 422). La
tabla también tiene una relación entrante: `productosporfactura.fkcodproducto`
→ eliminar un producto que aparezca en una factura fallará por FK (la API
mostrará el 500 con el error del motor — integridad referencial en acción).

## 3. Montar la BD para la v1

La BD es el servicio `postgres` del `docker-compose.yml` del proyecto
(ver [3_plan.md](3_plan.md) §5). Para levantarla sola durante las primeras
fases de construcción:

```powershell
docker compose up -d postgres      # desde la raíz del proyecto
```

Cadenas de conexión para la API (variable de entorno `DB_POSTGRES`):

```
# API corriendo LOCAL (venv + uvicorn), la BD publica el puerto 15435 al host:
postgresql+asyncpg://paradigmas:paradigmas123@localhost:15435/bdfacturas_postgres_local

# API corriendo EN el compose (la inyecta el docker-compose.yml, host interno):
postgresql+asyncpg://paradigmas:paradigmas123@postgres:5432/bdfacturas_postgres_local
```

Verificación: un cliente SQL debe ver **12 tablas** y `SELECT count(*) FROM
producto` debe dar **8**.

## 4. Qué toca la API en cada versión (la BD no cambia)

| Versión | Tablas que usa la API |
|---|---|
| **v1** | `producto` — nada más |
| v2 | + persona, empresa, cliente, vendedor, factura, productosporfactura (el trigger que ya vive en la BD empieza a trabajar) |
| v3–v4 | las mismas, contra más motores |
| v5 | la API genérica puede leer cualquiera de las 12 |
| v6 | el front las ve a través de las APIs |

**Regla de la v1:** el código solo puede nombrar la tabla `producto`. Que las
otras 11 existan no es invitación a usarlas — eso es alcance de las versiones
siguientes.
