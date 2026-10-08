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

**Qué hace:** enciende **seis** contenedores y devuelve la terminal (`-d` =
en segundo plano). Son los tres motores, el inicializador de SQL Server, la
API y la interfaz:

| Contenedor | Qué es | Puerto en su PC |
|---|---|---|
| `postgres` | El motor de la v1 | 15435 |
| `mariadb` | El segundo motor, de la v3 | 13335 |
| `sqlserver` | El tercero, de la v4 | 11435 |
| `sqlserver-init` | **Corre una vez y termina.** SQL Server no ejecuta solo los scripts montados: alguien tiene que entrar a correrlos | — |
| `api-facturas` | La API en Python / FastAPI | **8005** |
| `front-flask` | La interfaz en Flask + Jinja2 | **8046** |

```powershell
docker compose ps
```

> **Qué hay que ver:** cinco en `Up` y `sqlserver-init` en `Exited (0)`. Ese
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

## 3. Entrar — porque la API está cerrada

Pida el catálogo **sin identificarse** y mire qué pasa:

```powershell
Invoke-RestMethod http://localhost:8005/api/producto
```

> **Responde 401**, y está bien que lo haga. Desde la v3 los únicos dos
> endpoints abiertos son el diagnóstico y la puerta de entrada. Si esto
> respondiera datos, el control de acceso no existiría.

Entonces se entra, y el token se guarda en una variable:

```powershell
$s = Invoke-RestMethod -Method Post http://localhost:8005/api/sesion/entrar `
      -ContentType 'application/json' `
      -Body '{"email":"admin@correo.com","contrasena":"admin123"}'

$h = @{ Authorization = "Bearer $($s.token)" }
$s.roles        # Administrador
```

| La parte | Qué es |
|---|---|
| `$s.token` | El token firmado. Dura 60 minutos (`JWT_MINUTOS`) |
| `$h` | La cabecera que hay que mandar en **todas** las peticiones de aquí en adelante |
| `$s.roles` | Los nombres de los roles, que es lo que el token lleva adentro |

> **El token está firmado, no cifrado.** Péguelo en <https://jwt.io> y se lee
> entero: el correo, los roles y el vencimiento. Lo que la clave impide no es
> leerlo: es **fabricar uno**. Por eso ahí no va nada secreto — y por eso el
> **permiso** no viaja dentro, se consulta en cada petición.

---

## 4. Que responda datos

```powershell
Invoke-RestMethod http://localhost:8005/api/producto -Headers $h
```

**Qué hace:** pide el catálogo de productos. La API consulta el motor que
tenga configurado y devuelve las filas sembradas.

**El 403, que es el otro código de la v3.** Entre como vendedor y pida lo que
no le toca:

```powershell
$v = Invoke-RestMethod -Method Post http://localhost:8005/api/sesion/entrar `
      -ContentType 'application/json' `
      -Body '{"email":"vendedor1@correo.com","contrasena":"vendedor123"}'
$hv = @{ Authorization = "Bearer $($v.token)" }

Invoke-RestMethod http://localhost:8005/api/factura -Headers $hv   # 200
Invoke-RestMethod http://localhost:8005/api/usuario -Headers $hv   # 403
```

> **403 y no 401**, y la diferencia es el punto: 401 es «no sé quién es
> usted»; 403 es «sé quién es, y no puede». Lo decide
> `verificar_acceso_ruta`, **en la base de datos**, en cada petición.

**Y la documentación que se genera sola:**

```powershell
Start-Process http://localhost:8005/docs
```

> FastAPI arma ese Swagger **leyendo el código**: no hay un archivo que
> mantener al día. Ahí se pueden probar los endpoints con clics — primero
> `POST /api/sesion/entrar`, y el token se pega en el botón **Authorize**.

---

## 5. EL MOMENTO DE LA DEMOSTRACIÓN: cambiar de motor

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
Invoke-RestMethod http://localhost:8005/api/producto -Headers $h
```

> **Qué hay que ver:** `motor` ahora dice **`mariadb`**, y los productos son
> **los mismos**. Misma petición, misma respuesta, otro motor debajo.
>
> **Y un detalle que en vivo sorprende:** el token de antes **sigue
> sirviendo**. No se guardó en ninguna parte —la API no lleva lista de
> sesiones—, y lo firma la misma clave, que viene del entorno y no del motor.
> La sesión sobrevivió a un cambio de base de datos.
>
> Lo que **no** sobrevive es la contraseña: los usuarios están sembrados en
> los tres motores con el mismo hash, y por eso `admin123` funciona en los
> tres. Si una base se hubiera sembrado con otra clave, aquí se vería.

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

## 6. El maestro-detalle, que es la otra mitad

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
                  -ContentType "application/json" -Body $cuerpo -Headers $h
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
                  -ContentType "application/json" -Body $malo -Headers $h
```

> **Falla, y eso es lo correcto.** El mensaje dice qué producto y cuánto había.
> Y lo importante: **no queda media factura**. Se puede comprobar listando
> `GET /api/factura -Headers $h` — el encabezado tampoco se guardó.

**Anular una factura:**

```powershell
Invoke-RestMethod -Method Post -Uri http://localhost:8005/api/factura/1/anular `
                  -Headers $h
```

> Anular **no borra**: cambia el estado y devuelve el stock. Una factura
> borrada no se puede auditar.

---

## 7. La prueba que cierra la demostración: las mismas respuestas en los tres

Cambiar de motor no sirve de nada si lo que responde cambia. Esto es lo que se
midió el 7 de octubre de 2026, con `DB_PROVIDER` en los tres valores y sin
tocar una línea de código.

**Las diez consultas de la v4** —cada una cruzando cuatro o cinco tablas—:

| Consulta | postgres | mariadb | sqlserver |
|---|---|---|---|
| ventas-por-producto | 8 | 8 | 8 |
| ventas-por-cliente | 3 | 3 | 3 |
| ventas-por-vendedor | 3 | 3 | 3 |
| ventas-por-empresa | 2 | 2 | 2 |
| ticket-por-vendedor | 3 | 3 | 3 |
| productos-sin-vender | 0 | 0 | 0 |
| anulaciones-por-cliente | 2 | 2 | 2 |
| alcance-de-usuarios | 8 | 8 | 8 |
| interfaces-sin-usuarios | 0 | 0 | 0 |
| credito-contra-consumo | 6 | 6 | 6 |

Y el **ticket promedio** del primer vendedor da `3440000.0` en los tres — con
centavos, no truncado. Ese detalle no es gratis: en T-SQL, dividir un decimal
entre un entero **trunca**, y la consulta de SQL Server lleva un `CAST` que
las otras dos no necesitan ([`PLAN_V4.md`](dominio/PLAN_V4.md) §5).

**El control de acceso**, con los tres usuarios:

| | admin | vendedor1 | cliente1 |
|---|---|---|---|
| **postgres** | 200 · 200 · 200 | 403 · 200 · 403 | 200 · 403 · 403 |
| **mariadb** | 200 · 200 · 200 | 403 · 200 · 403 | 200 · 403 · 403 |
| **sqlserver** | 200 · 200 · 200 | 403 · 200 · 403 | 200 · 403 · 403 |

*(las tres rutas de cada celda: `/api/producto`, `/api/factura`, `/api/usuario`)*

> **Esta última tabla es la que destapó el único fallo grave de la versión**, y
> vale contarlo porque es la lección de medir: la primera vez, la fila de
> `mariadb` daba **200 en las nueve celdas**. Todo el mundo entraba a todo.
>
> El motivo: `verificar_acceso_ruta` devuelve el mismo JSON en los tres
> motores con el campo `tiene_acceso` de tres tipos distintos —booleano en
> PostgreSQL, número en SQL Server y **cadena** en MariaDB—, y en Python
> `bool("0")` es **True**.
>
> **Dos de los tres motores funcionaban por casualidad.** Leyendo el código no
> se veía; probando contra un solo motor, tampoco.

---

## 8. Apagar

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
