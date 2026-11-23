# Tutorial — Publicar el sistema en Render

**Hasta aquí el proyecto corrió en su máquina**, con un solo `docker compose up`:
seis contenedores —tres motores, la API y el front— que nacen juntos. **Aquí
sale a internet**, y lo primero que cambia es que las piezas dejan de vivir en
la misma casa.

| La pieza | Dónde va a quedar | Quién la ejecuta |
|---|---|---|
| **La base de datos** — PostgreSQL | **Neon**, Frankfurt | un servicio administrado |
| **La API** — Python / FastAPI | **Render** | una imagen Docker que construye Render |
| **El front** — Python / Flask | **Render** | otra imagen, **otro servicio** |

> **Sobre las capturas de este documento:** las de los paneles de **Neon y
> Render** se tomaron publicando **otro proyecto del curso**
> (`proyecto_diseno_de_software4`), porque esas pantallas son **exactamente
> las mismas** — lo que cambia son los nombres y las variables, y eso va
> escrito en tablas. Los pasos propios de este proyecto —FastAPI, el
> interruptor `DB_PROVIDER`, la cadena de `asyncpg`— **van sin capturas**.

> ### Qué está probado y qué no
>
> **Este tutorial todavía no se ha ejecutado de principio a fin con ESTE
> proyecto**, y el curso exige decirlo.
>
> | | |
> |---|---|
> | **Probado** | El camino Neon + Render, dos veces, con otros dos proyectos del curso |
> | **Probado** | La cadena `postgresql+asyncpg://...?ssl=require`, medida contra una base de datos de Neon real |
> | **Probado** | Los arreglos de este repositorio —el `${PORT:-8005}` del `Dockerfile`, el `PORT` antes que `PUERTO` del `app.py`, gunicorn— que son los mismos que ya corren publicados en otros dos proyectos |
> | **Sin ejecutar** | Los servicios de **este** proyecto en Render, y por lo tanto las direcciones y los registros que aparecen más abajo son **lo que se espera**, no lo que se midió |
>
> **Si usted lo reproduce y algo no coincide, el documento está equivocado y
> hay que corregirlo** — no al revés.

### Lo que cuesta: nada

| | Lo que da gratis | La letra menuda |
|---|---|---|
| **Neon** | 1 GB, hasta 2 CU | **se apaga sola** sin uso, y despierta con la primera consulta |
| **Render** | 750 horas de instancia al mes, `0.1 CPU` · `512 MB` | **se duerme a los 15 minutos** sin visitas. Las 750 horas son **de la cuenta**, repartidas entre todos sus servicios |

> **Y por qué la base de datos NO va en Render**, que también regala una: **el
> PostgreSQL gratuito de Render se borra a los 30 días.** Neon no caduca.

### Lo que este tutorial NO publica, y hay que decirlo

**De los tres motores, solo sale PostgreSQL.**

| Motor | Por qué |
|---|---|
| **PostgreSQL** | **se publica** — Neon, gratis y sin fecha de vencimiento |
| **MariaDB** | no hay MariaDB administrada gratis que dure: Aiven retiró la suya en diciembre de 2026 y las demás vienen recortadas. *(Para publicar con MariaDB, el camino es otro hospedaje — ver el tutorial de `proyecto_php4`.)* |
| **SQL Server** | no existe gratis administrado en ninguna parte |

> **El interruptor `DB_PROVIDER` sigue funcionando con los tres en el salón.**
> Lo que no hay es dónde publicar dos de ellos sin pagar — y eso **no es un
> defecto del diseño: es el mercado de hospedajes de 2026.**

### Antes de empezar

| | |
|---|---|
| **El repositorio en GitHub** | público. Render lo clona; **no lee su disco** |
| **El arreglo del puerto** | **ya está en el repositorio.** El paso 3 lo explica |
| **Tarjeta de crédito** | **ninguna** |

### Los pasos

| | Qué se hace | Dónde |
|---|---|---|
| **1** | La base de datos | Neon |
| **2** | El esquema y los datos | Neon |
| **3** | La cadena de conexión, y por qué la de Python no es la de siempre | su editor |
| **4** | El servicio de la API | Render |
| **5** | El front en Flask | Render |
| **6** | La prueba del sistema completo | el navegador |

---

## Paso 1 — La base de datos en Neon

```
https://neon.com
```

**`Sign up`**, en una ventana de incógnito —así no se cuela una sesión de
GitHub que no es la que quiere—.

![El formulario de proyecto nuevo en Neon](docs/tutorial_render/img/01_neon_crear_proyecto.png)

| La casilla | **Lo que se escribe** | Por qué |
|---|---|---|
| `Project name` | **`bdfacturas-paradigmas4`** | el nombre del proyecto, no el de la base de datos |
| `Region` | **`AWS Europe Central 1 (Frankfurt)`** | **donde quede la base de datos van a quedar los servicios de Render.** Y ojo: **la región no se cambia después** |
| `Services` | **solo `Postgres database`** | los otros cinco quedan apagados |

![El proyecto creado](docs/tutorial_render/img/02_neon_proyecto_creado.png)

> **Neon ofrece un bloque de texto para pegárselo a un agente de IA.** No lo
> use: conecta la aplicación solo, y lo que este tutorial enseña es
> justamente a leer y entender esa conexión.

![El tablero del proyecto](docs/tutorial_render/img/03_neon_tablero.png)

**La columna de la derecha es la ficha técnica.** Lo que importa:

| Lo que dice | Qué significa |
|---|---|
| **`IP restrictions: None set`** | cualquiera con la contraseña entra, desde donde sea. **La contraseña es toda la puerta** |
| **`Default compute: 0.25 ↔ 2 CU`** | un cuarto de CPU y 1 GB de RAM: sobra |
| **`Version: 18`** | PostgreSQL 18, contra el `postgres:16-alpine` del compose. El esquema no usa nada exclusivo de una versión — **pero eso se comprueba al importar** |

---

## Paso 2 — El esquema y los datos

**Menú de la izquierda: `SQL Editor`.**

![El editor de SQL de Neon](docs/tutorial_render/img/04_neon_sql_editor.png)

**El editor no llega vacío:** trae un ejemplo de Neon. Hay que **reemplazarlo**.

**Copie el archivo completo** —son 1.104 renglones— sin abrirlo, desde
PowerShell:

```powershell
Get-Content db\init.sql -Raw | Set-Clipboard
```

| La parte | Qué hace |
|---|---|
| `Get-Content ... -Raw` | lee el archivo **como un solo texto** |
| `\| Set-Clipboard` | lo deja en el portapapeles, listo para `Ctrl+V` |

> **El error que cae aquí:** copiar **la ruta** en vez del archivo. La ruta es
> el papelito con la dirección de la casa; el archivo es la casa.

**Clic en el editor → `Ctrl+A` → `Ctrl+V` → `Run`.**

![El script pegado en el editor](docs/tutorial_render/img/06_neon_script_pegado.png)

> **Si avisa que va a recortar el historial, ignórelo:** se ejecuta completo;
> lo que recorta es la copia que Neon guarda para mostrarle después.

**Y este archivo entra tal cual, sin tocarle nada** — el `CREATE DATABASE` ya
viene comentado, porque en Docker la base la crea el contenedor y aquí la creó
Neon.

**Comprobar:**

```sql
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
ORDER BY table_name;
```

![Las doce tablas](docs/tutorial_render/img/08_neon_doce_tablas.png)

**12 tablas.**

---

## Paso 3 — La cadena de conexión, y la trampa de Python

**Botón verde `Connect`**, arriba a la izquierda. **Deje `Connection pooling`
encendido** —esta API abre y cierra conexión en cada petición— y **oprima
`Hide password` antes de tomar cualquier captura.**

![El diálogo Connect, con la contraseña tapada](docs/tutorial_render/img/09_neon_conectar.png)

**Neon entrega esto:**

```
postgresql://neondb_owner:LA_CLAVE@ep-xxxx-pooler.c-7.eu-central-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require
```

**Y nuestra API no la entiende así.** Hay que convertirla:

```
postgresql+asyncpg://neondb_owner:LA_CLAVE@ep-xxxx-pooler.c-7.eu-central-1.aws.neon.tech/neondb?ssl=require
```

| El cambio | Por qué |
|---|---|
| agregar **`+asyncpg`** | dice **con qué driver** conecta SQLAlchemy. Sin eso busca otro —`psycopg2`, que no está instalado— y la API se cae al arrancar |
| `?sslmode=require` → **`?ssl=require`** | es el nombre que usa **asyncpg**. Con `sslmode` responde `TypeError: connect() got an unexpected keyword argument 'sslmode'` |
| borrar **`&channel_binding=require`** | asyncpg no conoce ese parámetro y falla igual |

> **Estas tres diferencias son el tipo de cosa que cuesta una tarde** si uno
> no sabe que existe: el mensaje de error habla de un argumento inesperado,
> no de que la cadena venga en otro dialecto. **Comprobado contra Neon antes
> de escribirlo.**

**Guárdela en un `.txt` fuera del repositorio:** trae la contraseña. En el
paso 4 se escribe **en el panel de Render**, no en un archivo del proyecto.

---

## Paso 4 — La API en Render

**`render.com` → `Get started`.** En incógnito.

![El registro de Render](docs/tutorial_render/img/10_render_registro.png)

![El tablero de Render](docs/tutorial_render/img/11_render_tablero.png)

> **Las 750 horas son de la cuenta, no de cada servicio.** Al terminar este
> tutorial va a tener **dos** servicios; como los gratuitos se duermen a los
> 15 minutos, solo gastan mientras alguien los usa.

**`+ New` → `Web Service`:**

![El menú New](docs/tutorial_render/img/12_render_new_web_service.png)

**Pestaña del medio, `Public Git Repository`**, y se pega la dirección:

![La dirección del repositorio pegada](docs/tutorial_render/img/13_render_repo_publico.png)

```
https://github.com/ccastro2050/proyecto_paradigmas4
```

**`Connect`.** Render clona, encuentra un `Dockerfile` y **detecta `Docker`
solo**.

![El formulario del servicio](docs/tutorial_render/img/14_render_formulario.png)

### 4.1 · Los campos

![Región, carpeta y plan](docs/tutorial_render/img/15_render_campos.png)

| La casilla | **Lo que se escribe** | Para qué |
|---|---|---|
| **`Name`** | `apifacturas-paradigmas4` | queda en la dirección: `apifacturas-paradigmas4.onrender.com` |
| `Language` | `Docker` | lo detectó solo |
| `Branch` | `main` | |
| **`Region`** | **`Frankfurt (EU Central)`** | donde quedó Neon |
| **`Root Directory`** | **`api_facturas`** | **el que más se olvida.** Sin él, Render busca el `Dockerfile` en la raíz del repositorio |
| **`Compute`** | **`$0 / month · Free`** | viene marcado el de **7 dólares** |
| `Health Check Path` (en `Advanced`) | **vacío** | con una ruta ahí, Render la golpea cada rato y **el servicio nunca se duerme** |
| `Dockerfile Path` | **no se toca** | este proyecto tiene **un solo** `Dockerfile` por carpeta |

### 4.2 · Las variables de entorno

| KEY | **VALUE** | Qué es |
|---|---|---|
| **`DB_PROVIDER`** | `postgres` | **el interruptor de la v4**: con cuál de los tres motores habla la API |
| **`DB_POSTGRES`** | la cadena traducida del paso 3 | **dónde está la base de datos** |
| **`JWT_CLAVE`** | oprima `Generate` | **la clave que firma el token.** Sin ella se usa la de aula, que está escrita en el repositorio — y cualquiera podría fabricarse un token |
| `JWT_MINUTOS` | `60` | cuánto dura la sesión. Opcional |

> **Y dos que NO se ponen:** `DB_MARIADB` y `DB_SQLSERVER`. El ensamblador
> lee **únicamente la variable del motor activo** —`os.environ[...]` del
> motor que diga `DB_PROVIDER`—, así que las otras dos ni se miran. **Si
> pusiera `DB_PROVIDER=mariadb` sin su cadena, la API se caería con un
> `KeyError`**, y eso es a propósito: mejor que arranque y mienta.

**`Deploy web service`.**

![La compilación](docs/tutorial_render/img/16_render_compilando.png)

**En el registro, el renglón que importa:**

```
Uvicorn running on http://0.0.0.0:10000
```

![El servicio vivo](docs/tutorial_render/img/17_render_vivo.png)

> **10000, no 8005.** Render impone el puerto con la variable `PORT`, y el
> `Dockerfile` de este proyecto lo traduce:
>
> ```dockerfile
> CMD ["sh", "-c", "exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8005}"]
> ```
>
> **El `sh -c` no es adorno.** La forma corta —`["uvicorn", "--port",
> "$PORT"]`— no pasa por un shell, así que `$PORT` llegaría **literal**, con
> el signo de dólar. La aplicación arrancaría en el 8005, Render no
> encontraría nada en el 10000 y **reportaría el servicio como caído con la
> API viva adentro.**

### 4.3 · Probarla

**FastAPI trae su documentación de fábrica:**

```
https://apifacturas-paradigmas4.onrender.com/docs
```

**Y la raíz dice contra qué motor está hablando:**

```powershell
Invoke-RestMethod https://apifacturas-paradigmas4.onrender.com/
```

```
mensaje : API Facturas funcionando
motor   : postgres
```

**La prueba que de verdad toca la base de datos** es iniciar sesión:

```powershell
Invoke-RestMethod -Method Post -Uri https://apifacturas-paradigmas4.onrender.com/api/sesion `
  -ContentType "application/json" `
  -Body '{"email":"admin@correo.com","contrasena":"admin123"}'
```

> **La primera llamada del día tarda** hasta un minuto: están despertando **el
> servicio de Render y la base de datos de Neon**, uno detrás del otro.

---

## Paso 5 — El front en Flask

**El mismo repositorio otra vez.** Lo único que cambia de verdad es la carpeta.

**`+ New` → `Web Service` → `Public Git Repository` → la misma dirección.**

| La casilla | **Lo que se escribe** |
|---|---|
| `Name` | `facturas-flask-paradigmas4` |
| `Region` | **`Frankfurt (EU Central)`** — al lado de la API |
| **`Root Directory`** | **`front_flask`** ← la única diferencia con el paso 4 |
| `Compute` | **`$0 / month · Free`** |

**Variables de entorno:**

| KEY | **VALUE** | Qué es |
|---|---|---|
| **`API_FACTURAS_URL`** | `https://apifacturas-paradigmas4.onrender.com` | **a qué API le habla.** Sin esto busca en `localhost:8005`, que dentro del contenedor es él mismo |
| **`CLAVE_SESION`** | oprima `Generate` | firma la cookie donde el front guarda el token |

> **Tres errores al escribir esa dirección, y ninguno dice lo que pasa:** sin
> `https://` adelante, con **barra al final** —el front armaría
> `...onrender.com//api/sesion`, con dos barras, y recibiría `404`—, o
> copiada a ojo.

> **Ojo con el nombre de la variable de la cookie:** el `docker-compose.yml`
> de este proyecto pone `FLASK_SECRET`, pero **el código lee `CLAVE_SESION`**
> (`app.py`). En Render hay que poner **`CLAVE_SESION`**; con la otra, el
> front arranca igual pero usando la clave por defecto.

**En el registro, los dos renglones que prueban que el `Dockerfile` quedó
bien:**

```
Starting gunicorn 23.0.0
Listening at: http://0.0.0.0:10000
```

| | Por qué |
|---|---|
| **gunicorn**, y no el servidor de Flask | la imagen trae `DEPURAR=0`. El de Flask atiende una petición a la vez y su depurador en internet deja ejecutar código |
| **el 10000** | `app.py` lee `PORT` **antes** que `PUERTO`. El mismo código corre en Docker (8046) y aquí |

---

## Paso 6 — La prueba del sistema completo

```
https://facturas-flask-paradigmas4.onrender.com
```

**Entre con `admin@correo.com` / `admin123`** y abra `Productos`.

### Lo que recorre esa pantalla

```
su navegador
   |  https
front en Flask      Render, Frankfurt     (Python, en Docker)
   |  https
API en FastAPI      Render, Frankfurt     (Python, en Docker)
   |  tls
base de datos       Neon, Frankfurt       (PostgreSQL 18)
```

| | |
|---|---|
| **Tres proveedores** | Render, Neon y GitHub |
| **Dos imágenes Docker** | construidas por Render a partir de dos `Dockerfile` del mismo repositorio |
| **Un solo sistema** | y ninguna pieza sabe cómo está hecha la otra |

> **La primera carga del día va a tardar**, y esta vez hay **tres cosas
> dormidas en fila**: el front, la API y la base de datos.

---

## Si algo falla

| Lo que ve | Qué revisar |
|---|---|
| `Deploy failed` | lea el registro **de abajo hacia arriba**: el error de verdad suele estar varios renglones antes del final |
| **`KeyError: 'DB_POSTGRES'`** | falta la variable, o está escrita con otro nombre |
| **`TypeError: connect() got an unexpected keyword argument 'sslmode'`** | la cadena quedó con `sslmode` en vez de **`ssl`** (paso 3) |
| **`InvalidRequestError: Can't load plugin: sqlalchemy.dialects:postgres`** | le falta **`+asyncpg`** a la cadena |
| La API responde pero `motor` dice otra cosa | `DB_PROVIDER`. Por defecto es `postgres`; si alguien la puso mal, la API intenta hablarle a un motor que aquí no existe |
| El front abre y avisa que no conecta | `API_FACTURAS_URL`: sin `https://`, con barra al final, o mal escrita |
| El front entra pero pierde la sesión al refrescar | puso `FLASK_SECRET` en vez de **`CLAVE_SESION`** |
| Tarda 50 segundos | está despertando. **No es un error**, es el plan gratuito |
| `relation "producto" does not exist` | falta correr `db/init.sql` en Neon (paso 2) |

---

## Lo que quedó demostrado

| | |
|---|---|
| **El motor es configuración, no código** | una variable —`DB_PROVIDER`— decide, y el resto del sistema ni se entera |
| **El puerto no lo decide la aplicación** | lo impone la plataforma, y el programa obedece. Es el fallo más común al publicar en contenedores |
| **Un `Dockerfile` es la receta** | Render no sabe que esto es FastAPI: lee el archivo y construye |
| **Los secretos viven en el panel** | por eso el repositorio puede ser público |
| **Lo que se puede publicar gratis no lo decide el diseño** | lo decide el mercado de hospedajes del año en que uno esté: de tres motores, hoy solo uno tiene dónde vivir sin pagar |

---

**Versión 0.9 — escrito el 23 de noviembre de 2026, SIN ejecutar.** El camino
está probado con otros dos proyectos del curso y los arreglos de este
repositorio también; lo que falta es correrlo aquí. **Cuando se ejecute, esta
versión pasa a 1.0, las capturas prestadas se reemplazan por las propias y las
direcciones dejan de ser un ejemplo.**
