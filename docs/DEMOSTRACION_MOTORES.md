# La demostración del cambio de motor, paso a paso

> ### ⚠️ Ojo con lo que demuestra esto
>
> **Las versiones 1 a 4 del curso son PostgreSQL, y solo PostgreSQL.** Los
> otros dos motores son el **adelanto de la v5**, que está fuera de las cuatro
> ([el mapa](spec_kit/versiones/0_mapa_versiones.md) lo explica).
>
> Así que esta demostración **no muestra la v4**: muestra la v5 adelantada —
> la misma API, con el mismo contrato, hablando con tres motores distintos y
> cambiando de uno a otro **sin tocar una línea de código**. Vale la pena
> mostrarla, pero diciendo qué es.
>
> Todo lo de aquí sale del `docker-compose.yml` y de los controladores de este
> repositorio. **Los comandos son de PowerShell.**

---

## 0. Antes de empezar

**Docker Desktop tiene que estar encendido.** Si no lo está, el primer comando
falla con *«cannot find the file specified»* y no es culpa del proyecto.

```powershell
cd C:\Users\fcl\OneDrive\Desktop\proyectos_usbmed\2026_2\proyecto_paradigmas4
docker version          # si responde, el demonio está arriba
```

---

## 1. Levantar el sistema

```powershell
docker compose up -d
```

**Qué hace:** enciende **cinco** contenedores y devuelve la terminal (`-d` =
en segundo plano). Son los tres motores, el inicializador de SQL Server y la
API:

| Contenedor | Qué es | Puerto en su PC |
|---|---|---|
| `postgres` | El motor de la v1 | 15435 |
| `mariadb` | El segundo motor, de la v3 | 13335 |
| `sqlserver` | El tercero, de la v4 | 11435 |
| `sqlserver-init` | **Corre una vez y termina.** SQL Server no ejecuta solo los scripts montados: alguien tiene que entrar a correrlos | — |
| `api-facturas` | La API en Python / FastAPI | **8005** |

```powershell
docker compose ps
```

> **Qué hay que ver:** cuatro en `Up` y `sqlserver-init` en `Exited (0)`. Ese
> cero importa: salió bien. Si saliera con otro número, la base no quedó
> sembrada.

**La primera vez tarda**, porque los motores tienen que crear sus bases y
sembrarlas. Las siguientes arrancan en segundos: los datos quedan en los
volúmenes `pgdata`, `mariadbdata` y `mssqldata`.

---

## 2. ¿Está viva, y con cuál motor está hablando?

```powershell
Invoke-RestMethod http://localhost:8005/
```

**Qué responde:**

```json
{ "mensaje": "API Facturas funcionando", "version": "v4",
  "motor": "postgres", "documentacion": "/docs" }
```

> **`motor` es el dato de la demostración.** Lo lee de la variable
> `DB_PROVIDER`, y si nadie la puso vale `postgres`. Guárdelo: dentro de un
> minuto va a decir otra cosa **sin que hayamos tocado el código**.

---

## 3. Que responda datos

```powershell
Invoke-RestMethod http://localhost:8005/api/producto
```

**Qué hace:** pide el catálogo de productos. La API consulta el motor que
tenga configurado y devuelve las filas sembradas.

**Y la documentación que se genera sola:**

```powershell
Start-Process http://localhost:8005/docs
```

> FastAPI arma ese Swagger **leyendo el código**: no hay un archivo que
> mantener al día. Ahí se pueden probar los endpoints con clics.

---

## 4. EL MOMENTO DE LA DEMOSTRACIÓN: cambiar de motor

Esto es lo que hay que mostrar despacio, porque es lo que enseña la versión.

```powershell
$env:DB_PROVIDER="mariadb"
docker compose up -d api-facturas
```

**Qué hace:** pone la variable en **su terminal** y vuelve a crear **solo** el
contenedor de la API, que la lee al arrancar. Los motores ni se enteran: siguen
encendidos.

```powershell
Invoke-RestMethod http://localhost:8005/
Invoke-RestMethod http://localhost:8005/api/producto
```

> **Qué hay que ver:** `motor` ahora dice **`mariadb`**, y los productos son
> **los mismos**. Misma petición, misma respuesta, otro motor debajo.

Y el tercero:

```powershell
$env:DB_PROVIDER="sqlserver"
docker compose up -d api-facturas
Invoke-RestMethod http://localhost:8005/
```

**Para volver al de siempre:**

```powershell
$env:DB_PROVIDER="postgres"
docker compose up -d api-facturas
```

> ### La pregunta que hay que hacerle al curso aquí
>
> *¿Cuántas líneas de código cambiamos para pasar de PostgreSQL a SQL Server?*
>
> **Ninguna.** Cambió una variable de entorno. Eso es lo que significa que el
> servicio dependa de una **abstracción** del repositorio y no de un motor: la
> pieza que sabe de SQL se reemplaza, y lo de arriba no se entera.
>
> Se puede mostrar en el código: `api_facturas/repositorios/abstracciones/`
> tiene las interfaces, y al lado está la implementación de cada motor.

---

## 5. El maestro-detalle, que es la otra mitad

Una factura y sus renglones **en un solo envío**:

```powershell
$cuerpo = @{
  fkidcliente  = 1
  fkidvendedor = 1
  productos    = @(
    @{ codigo = "PR001"; cantidad = 2 },
    @{ codigo = "PR003"; cantidad = 3 }
  )
} | ConvertTo-Json -Depth 5

Invoke-RestMethod -Method Post -Uri http://localhost:8005/api/factura `
                  -ContentType "application/json" -Body $cuerpo
```

**Qué hay que ver en la respuesta:** el **total** y los **subtotales** vienen
calculados, y nadie los envió. Los puso la base de datos.

**Y la prueba que de verdad convence** — pedir más de lo que hay:

```powershell
$malo = @{
  fkidcliente = 1; fkidvendedor = 1
  productos = @(@{ codigo = "PR001"; cantidad = 9999 })
} | ConvertTo-Json -Depth 5

Invoke-RestMethod -Method Post -Uri http://localhost:8005/api/factura `
                  -ContentType "application/json" -Body $malo
```

> **Falla, y eso es lo correcto.** El mensaje dice qué producto y cuánto había.
> Y lo importante: **no queda media factura**. Se puede comprobar listando
> `GET /api/factura` — el encabezado tampoco se guardó.

**Anular una factura:**

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:8005/api/factura/1/anular
```

> Anular **no borra**: cambia el estado y devuelve el stock. Una factura
> borrada no se puede auditar.

---

## 6. Apagar

```powershell
docker compose down
```

**Qué hace:** apaga y borra los contenedores, **y conserva los datos** en los
volúmenes. La próxima vez arranca con todo donde estaba.

> ⚠️ **`docker compose down -v` NO.** Esa `-v` borra los volúmenes, y con
> ellos las tres bases de datos sembradas. No hay deshacer.

---

## Si algo sale mal

| Qué pasa | Qué es | Qué hacer |
|---|---|---|
| `cannot find the file specified` al correr `docker` | Docker Desktop está apagado | Encenderlo y esperar a que el icono deje de moverse |
| La API responde pero `/api/producto` da error | El motor todavía está sembrando | `docker compose logs -f api-facturas` y esperar |
| `sqlserver-init` en `Exited (1)` | El script no corrió | `docker compose logs sqlserver-init` dice en qué línea |
| El puerto 8005 está ocupado | Otro proyecto lo tomó | `netstat -ano \| findstr :8005` para ver quién |
