# Arranque y verificación — Versión 4: el aplicativo completo

> **Versión 4** del desarrollo incremental ([mapa de versiones](../0_mapa_versiones.md)).
> Rige la constitución: [../../1_constitution.md](../../1_constitution.md).
> **Acumulativa:** contiene TODO lo de v1 a v3 — los 70 endpoints existentes no
> se tocan y sus contratos siguen vigentes tal cual. La v4 **suma 10**.
>
> | Documento de esta versión | Contenido |
> |---|---|
> | [2_spec.md](2_spec.md) | QUÉ agrega la v4 y sus criterios de aceptación |
> | [3_plan.md](3_plan.md) | CÓMO: la capa de consultas y el tablero |
> | [4_research.md](4_research.md) | Decisiones y alternativas *(lectura opcional)* |
> | [5_data_model.md](5_data_model.md) | La MISMA bdfacturas: cero tablas nuevas |
> | [6_contracts.md](6_contracts.md) | Los 10 endpoints de `/api/consultas` |
> | **7_quickstart.md** (este) | Arranque y el smoke test de las diez |
> | [8_tasks.md](8_tasks.md) | Orden de construcción por fases verificables |
> | [9_checklist.md](9_checklist.md) | Lo que tiene que estar antes de cerrar |
> | [GUIA_IA4.md](GUIA_IA4.md) | Construirla con IA, sobre su proyecto v3 |

---

## 1. Levantar

```powershell
docker compose up -d --build
```

La primera vez tarda unos minutos. Al terminar quedan **seis contenedores**:
los tres motores, el inicializador de SQL Server —que corre una vez y sale con
`Exited (0)`—, la API y la interfaz gráfica.

> **De la v1 a la v4 el motor es PostgreSQL.** Los otros dos están encendidos
> porque este repositorio es el ejemplo del profesor y trae la v5 proyectada;
> en el proyecto de un estudiante basta con PostgreSQL.

> **La API tarda en responder aunque el contenedor diga `Up`.** `uvicorn --reload`
> compila al encender, y hasta que termine el puerto no contesta. Un `curl`
> apurado devuelve «connection refused» y parece una falla.

## 2. CRITERIO 2 — las diez consultas

Primero el token. **En PowerShell se usa `Invoke-RestMethod`, no `curl`**: el
`curl` de PowerShell es un alias de `Invoke-WebRequest` y **no acepta las
mismas banderas** — el comando parece correcto y falla por otra razón.

```powershell
$s = Invoke-RestMethod -Uri "http://localhost:8005/api/sesion/entrar" -Method Post `
     -ContentType "application/json" `
     -Body '{"email":"admin@correo.com","contrasena":"admin123"}'
$t = $s.token
```

Y ahora las diez:

```powershell
$r = Invoke-RestMethod -Uri "http://localhost:8005/api/consultas/ventas-por-producto" -Headers @{Authorization="Bearer $t"}
Write-Host "ventas-por-producto        $($r.total) filas"
$r = Invoke-RestMethod -Uri "http://localhost:8005/api/consultas/ventas-por-cliente" -Headers @{Authorization="Bearer $t"}
Write-Host "ventas-por-cliente         $($r.total) filas"
$r = Invoke-RestMethod -Uri "http://localhost:8005/api/consultas/ventas-por-vendedor" -Headers @{Authorization="Bearer $t"}
Write-Host "ventas-por-vendedor        $($r.total) filas"
$r = Invoke-RestMethod -Uri "http://localhost:8005/api/consultas/ventas-por-empresa" -Headers @{Authorization="Bearer $t"}
Write-Host "ventas-por-empresa         $($r.total) filas"
$r = Invoke-RestMethod -Uri "http://localhost:8005/api/consultas/ticket-por-vendedor" -Headers @{Authorization="Bearer $t"}
Write-Host "ticket-por-vendedor        $($r.total) filas"
$r = Invoke-RestMethod -Uri "http://localhost:8005/api/consultas/productos-sin-vender" -Headers @{Authorization="Bearer $t"}
Write-Host "productos-sin-vender       $($r.total) filas"
$r = Invoke-RestMethod -Uri "http://localhost:8005/api/consultas/anulaciones-por-cliente" -Headers @{Authorization="Bearer $t"}
Write-Host "anulaciones-por-cliente    $($r.total) filas"
$r = Invoke-RestMethod -Uri "http://localhost:8005/api/consultas/alcance-de-usuarios" -Headers @{Authorization="Bearer $t"}
Write-Host "alcance-de-usuarios        $($r.total) filas"
$r = Invoke-RestMethod -Uri "http://localhost:8005/api/consultas/interfaces-sin-usuarios" -Headers @{Authorization="Bearer $t"}
Write-Host "interfaces-sin-usuarios    $($r.total) filas"
$r = Invoke-RestMethod -Uri "http://localhost:8005/api/consultas/credito-contra-consumo" -Headers @{Authorization="Bearer $t"}
Write-Host "credito-contra-consumo     $($r.total) filas"
```

**Las diez tienen que responder.** Dos pueden decir `0 filas` —la 6 y la 9— y
eso **también es pasar**: ver [2_spec.md](2_spec.md) criterio 7.

> **Si una responde 500 hablando de `STRING_AGG` o de sintaxis**, es el
> dialecto: la consulta 8 no se escribe igual en los tres motores. Ver
> [4_research.md](4_research.md) §D4.
>
> **Y si el `ticket_promedio` sale sin centavos** —un número redondo— la
> consulta 5 está sin el `CAST`, y ese es el tropiezo peligroso de esta
> versión: **no falla, miente**. Solo pasa contra SQL Server, donde dividir
> un decimal entre un entero trunca.

## 3. CRITERIO 5 — el tablero

Abra **http://localhost:8046/tablero**.

| Lo que hay que ver | Si no se ve |
|---|---|
| Las **diez** secciones, con su título y qué tablas cruza | Falta registrar algo: ver [8_tasks.md](8_tasks.md) |
| Las **barras** de la consulta 1, con anchos distintos | El tope se calculó mal, o las filas llegaron vacías |
| **Un solo tiempo de espera**, no diez seguidos | Se pidieron en fila. Ver [3_plan.md](3_plan.md) §3.1 |

## 4. CRITERIO 4 — token y permiso

```powershell
# sin token -> 401
Invoke-WebRequest -Uri "http://localhost:8005/api/consultas/ventas-por-producto" `
  -SkipHttpErrorCheck | Select-Object StatusCode
```

Y el **403**, que es la prueba que de verdad cierra el criterio: quítele el
permiso `/home` al rol del usuario con el que entró —`DELETE
/api/rutarol/{id_ruta}/{id_rol}`— y pida la consulta otra vez **con el mismo
token, sin volver a identificarse**. Tiene que responder **403**, porque el
permiso se consulta en cada petición y no se lee del token.

Después se lo devuelve con `POST /api/rutarol` y vuelve a dar 200. Ese ir y
venir, con un token que no se tocó, es la demostración completa.

## 5. CRITERIO 8 — el tablero reacciona

Es la prueba que distingue un tablero de una lámina:

| Paso | Qué tiene que pasar |
|---|---|
| **1.** Abra el tablero y anote el ingreso del producto más vendido | — |
| **2.** Vaya a la interfaz de facturas y **anule** una factura de ese producto | — |
| **3.** Vuelva al tablero | La consulta **7** —anulaciones— **se llena**, y el ingreso del paso 1 **baja** |

> Si el número no se mueve, el tablero está leyendo de otro lado: de una copia,
> de un caché, o de datos escritos a mano.

## 6. CRITERIO 1 — la regresión

**Y es obligatoria.** El smoke test de la v1, el de la v2 y el de la v3,
completos. La v4 no tocó ningún endpoint anterior, y **eso hay que
comprobarlo**, no suponerlo.
