# Proyecto Paradigmas — construcción por versiones

Proyecto del curso **Paradigmas de Programación** (USB Medellín). Aquí NO se
descarga un sistema terminado: **se construye un sistema real por versiones**,
guiado por especificaciones. El repositorio siempre contiene la **versión en
curso, funcionando** — usted la ejecuta, la estudia y luego la **reconstruye
desde cero** en su propio proyecto.

> 🐳 Esta variante corre sobre **Docker**. Para las salas SIN Docker existe
> el repositorio gemelo
> [proyecto_paradigmas_sin_docker](https://github.com/ccastro2050/proyecto_paradigmas_sin_docker)
> (PostgreSQL instalado + venv) — misma API, misma spec, otra infraestructura.

### Qué hay hoy en el repositorio (v4, cerrada)

| | Cuánto | Dónde se ve |
|---|---|---|
| **La base de datos** | 12 tablas · 1 disparador · 16 procedimientos | `db/init.sql` |
| **La API** | 15 controladores · **45 rutas, 91 operaciones** | http://localhost:8005/docs |
| **Las tres capas** | 15 servicios + 15 contratos · **42 repositorios** + 14 contratos | `api_facturas/` |
| **El control de acceso** | token firmado · 401 y 403 en cada petición | `api_facturas/autorizacion/` |
| **Las consultas de la v4** | **10**, cada una cruzando 4 o 5 tablas | http://localhost:8046/tablero |
| **La interfaz** | **14 pantallas**, una por recurso | http://localhost:8046 |
| **Los tres motores** | la MISMA API contra PostgreSQL, MariaDB y SQL Server | [`DEMOSTRACION_MOTORES.md`](docs/DEMOSTRACION_MOTORES.md) |

**Los 42 repositorios contra los 14 contratos son la arquitectura en un
número:** cada contrato tiene tres implementaciones —una por motor— y arriba
nadie sabe cuál está puesta. Cambiar de motor es cambiar **una variable de
entorno**, no una línea de código.

---

## 1. Cómo le trabaja el estudiante (léame primero)

### Qué necesita instalado (una sola vez)

| Herramienta | Para qué |
|---|---|
| **Git** | Clonar el repositorio y traer versiones nuevas |
| **Docker Desktop** | La base de datos corre en un contenedor (no se instala PostgreSQL) |
| **Python 3.12** | El lenguaje de la API |
| **VS Code** | El editor — y su terminal integrada (*Terminal → New Terminal*) |

### Primera vez: cargar y EJECUTAR la versión (un solo comando)

En la terminal integrada de VS Code (*Terminal → New Terminal*, PowerShell):

> ⚠️ **ANTES de clonar — solo si usted ya corrió OTRO proyecto de estos
> cursos en este PC:** puede quedar un contenedor viejo encendido ocupando
> el puerto 8005 (pasa al reiniciar el PC: la API vieja revive sin su
> base de datos y "secuestra" el puerto — el contenedor huérfano). El
> síntoma: Swagger abre, pero todo responde 500 con *"No address
> associated with hostname"*, y usted cree que el error es de ESTE
> proyecto cuando en realidad está hablando con el viejo. Verifíquelo y
> apáguelo primero:
>
> **En este curso los dos comandos se copian y se pegan tal cual.** Pero no
> por la misma razón, y la diferencia importa:
>
> | | ¿Se cambia? |
> |---|---|
> | `$_` | **Nunca.** Es sintaxis de PowerShell — significa «cada uno de los que vinieron por la tubería». Si lo reemplaza por algo, deja de funcionar |
> | `proyecto_` | **Aquí no**, porque todas las carpetas de estos cursos se llaman `proyecto_algo`. Pero es **texto de búsqueda**: en otro proyecto habría que poner el suyo |
>
> **O sea: este comando no es universal.** Funciona tal cual en estos cursos
> porque Docker le pone al contenedor el nombre de la carpeta de la que
> salió, y todas empiezan igual. Si mañana trabaja en una carpeta llamada
> `taller_php`, el filtro sería `name=taller_`.
>
> **¿Y cómo sabría qué poner?** Corriendo `docker ps` sin filtro, mirando los
> nombres de la columna `NAMES` y escogiendo el pedazo que tengan en común.
>
> **Paso 1 — VERIFICAR.** ¿Quedó algo del curso encendido?
>
> ```powershell
> docker ps --filter "name=proyecto_"
> ```
>
> | La parte | Qué significa |
> |---|---|
> | `docker ps` | Lista los contenedores **encendidos** |
> | `--filter` | «No me muestre todo, filtre» |
> | `name=` | Filtrar **por nombre**. Es palabra de Docker: también existen `status=` y `ancestor=` |
> | `proyecto_` | **El texto a buscar.** Esto no es sintaxis: lo escogió quien escribió el comando |
>
> **Ojo con esa última parte.** El comando se copia tal cual y funciona, pero
> `proyecto_` no es una palabra mágica: es el texto por el que se busca.
> Funciona porque **todas** las carpetas de estos cursos se llaman
> `proyecto_algo`, y Docker le pone al contenedor el nombre de la carpeta de
> la que salió. Si su carpeta se llamara `taller_php`, el filtro sería
> `name=taller_`.
>
> Si hay algo, se ve así:
>
> ```
> NAMES                                 STATUS                    PORTS
> proyecto_paradigmas4-api-facturas-1   Up 2 hours                0.0.0.0:8005->8005/tcp
> proyecto_paradigmas4-postgres-1       Up 2 hours (healthy)      0.0.0.0:15435->5432/tcp
> ```
>
> **Si no hay nada, sale solo el encabezado** —`NAMES  STATUS  PORTS`— y
> ninguna línea debajo. En ese caso no tiene que limpiar nada: siga.
>
> **Paso 2 — LIMPIAR.** Apaga de una vez todos los del curso:
>
> ```powershell
> docker ps --filter "name=proyecto_" -q | ForEach-Object { docker stop $_ }
> ```
>
> | La parte | Qué significa |
> |---|---|
> | `docker ps --filter …` | Lo mismo de arriba: los del curso que están encendidos |
> | `-q` | *quiet*. En vez de la tabla, imprime **solo el identificador** de cada uno |
> | `\|` | La tubería: entrega esa lista al comando que sigue |
> | `ForEach-Object { … }` | «Para **cada uno** de los que llegaron, haga esto» |
> | `$_` | **Cada uno de ellos.** Es de PowerShell: no se reemplaza por nada |
> | `docker stop $_` | Apaga ese contenedor |
>
> En una frase: **«de los contenedores del curso que estén encendidos, tome
> el identificador de cada uno y apáguelo».**
>
> Va imprimiendo el identificador de cada uno que apaga. Para comprobar que
> quedó limpio, repita el paso 1: debe salir solo el encabezado.
>
> **Qué efecto tiene:** apaga los contenedores. **No borra nada** — los datos
> quedan en sus volúmenes y cada proyecto se vuelve a encender con su
> `docker compose up -d`. Funciona aunque ya no tenga la carpeta vieja.
> También sirve el botón **Stop** de Docker Desktop, uno por uno.
>
> Solo entonces continúe.

```powershell
git clone https://github.com/ccastro2050/proyecto_paradigmas4.git
cd proyecto_paradigmas4
docker compose up -d --build
```

**Eso es todo.** La primera vez tarda unos minutos (descarga imágenes). Al
terminar quedan corriendo la base de datos (bdfacturas completa) y la API:

| Qué | Dónde |
|---|---|
| **La interfaz gráfica** (Flask) | **http://localhost:8046** |
| **API Facturas — Swagger** (probar los endpoints) | http://localhost:8005/docs |
| Diagnóstico | http://localhost:8005/ |
| PostgreSQL (para DBeaver/pgAdmin, opcional) | `localhost:15435` · `paradigmas`/`paradigmas123` |

> **Son DOS procesos, y conviene verlo:** la interfaz en 8046 y la API en
> 8005, en contenedores distintos. Apague la API con
> `docker compose stop api-facturas` y abra la interfaz: **sigue en pie**, con
> su aviso y sin una sola fila. Eso es la separación de capas a nivel de
> sistema, no de carpetas.

### Lo primero: ENTRAR

Desde la v3 la API está **cerrada**. Quien llegue sin identificarse recibe
**401**, y eso incluye Swagger:

| Paso | Qué hacer |
|---|---|
| **1** | Abra http://localhost:8005/docs y busque **`POST /api/sesion/entrar`** |
| **2** | *Try it out* con `{"email": "admin@correo.com", "contrasena": "admin123"}` |
| **3** | Copie el `token` de la respuesta |
| **4** | Botón **Authorize** (arriba a la derecha) y pegue `Bearer <el token>` |

Ahora sí responden los demás endpoints. En la interfaz gráfica (8046) es más
corto: la pantalla de entrada pide los mismos datos.

**Las contraseñas están escritas a propósito**, y conviene entender por qué:
en la base de datos se guardan con **hash bcrypt**, y de un hash no se puede
volver a la clave —eso es lo que lo hace un hash—. Sin tenerlas anotadas en
algún lado, no habría forma de entrar a probar:

| Usuario | Contraseña | A qué llega |
|---|---|---|
| `admin@correo.com` | `admin123` | A las 15 rutas |
| `vendedor1@correo.com` | `vendedor123` | Solo a inicio, facturas y clientes |
| `cliente1@correo.com` | `cliente123` | Solo a inicio y productos |

> **Con esos tres se comprueba el 403**, que es el criterio que importa:
> entre como `vendedor1` y pida `/api/usuario`. Responde **403**, no 401 —
> «sé quién es usted, y no puede»—. Y **no** porque la interfaz esconda el
> botón: escribiendo la dirección a mano. Las otras cinco claves están en
> `db/init.sql`, junto a los datos sembrados.

Pruebe también, ya con el token: PUT a `/api/producto/PR001` con solo
`{"stock": 99}` → **422**; el mismo body en PATCH → **200**. Esa diferencia
es parte de lo que enseña la v1, y sigue viva en la v4.

### Los días siguientes (volver a encender)

```powershell
docker compose up -d        # segundos; los datos se conservan
```

### Cuando hay cambios

| Qué cambió | Qué hacer |
|---|---|
| **Usted edita un `.py`** | **Nada** — el código está montado como volumen y `--reload` reinicia la API sola al guardar |
| **El profesor publicó una versión nueva** | `git pull` y `docker compose up -d --build` |
| **Cambió `requirements.txt` o un `Dockerfile`** | `docker compose up -d --build` (reconstruye la imagen) |
| **Quiere resetear la BD** a sus datos originales | `docker compose down -v` y luego `docker compose up -d` (⚠️ borra los datos) |
| **Apagar todo** | `docker compose down` (los datos se conservan) |

### Y ahora, SU trabajo: reconstruirla desde cero

Ejecutar la versión del repo es solo el punto de partida. Lo que se evalúa es
**reconstruirla usted mismo, en una carpeta propia (fuera del clon)**,
siguiendo las especificaciones — con o sin ayuda de IA:

> 🤖 **[Guía para construir la versión con IA](docs/conceptos/GUIA_IA.md)** — los dos
> caminos con su prompt listo para copiar: **chat web** (Gemini, DeepSeek,
> ChatGPT) e **IDE agéntico** (Antigravity, Cursor, Claude Code).

### Conceptos resumidos (los que acaba de usar)

| Concepto | En una frase |
|---|---|
| **Clonar** | Descargar el repositorio con su historial; `git pull` trae lo nuevo |
| **Contenedor** | BD y API corren en "cajas" de Docker: nada que instalar, se borran y recrean sin miedo |
| **docker compose** | UN archivo declara todo el sistema y UN comando lo levanta (`up -d`) |
| **Volumen** | Donde viven los datos: `down` los conserva, `down -v` los borra (reset) |
| **--reload** | El código está montado en el contenedor: guardar un archivo recarga la API sola |
| **Swagger (/docs)** | La documentación interactiva: probar la API desde el navegador |
| **Spec kit** | Los documentos que dicen QUÉ/CÓMO/EN QUÉ ORDEN — la fuente de verdad |
| **Versión / tag** | Un incremento cerrado y verificado (`v1`, `v2`, …): se avanza solo en verde |

> Detalle de todos estos conceptos: [docs/CONCEPTOS_DOCKER.md](docs/conceptos/CONCEPTOS_DOCKER.md).

---

## 2. Estructura del repositorio

Qué es cada carpeta y cada archivo, y para qué sirve:

```
proyecto_paradigmas4/
├── docker-compose.yml           # TODO el sistema declarado: tres motores +
│                                #   la API + el front (el "un solo comando")
├── db/
│   ├── init.sql                 # bdfacturas COMPLETA en PostgreSQL: 12 tablas,
│   │                            #   1 disparador, 16 procedimientos y los datos.
│   │                            #   Se ejecuta solo la PRIMERA vez (volumen vacío)
│   ├── init_mariadb.sql         # La MISMA base en MariaDB      (para la v5)
│   ├── bdfacturas_sqlserver.sql # La MISMA base en SQL Server   (para la v5)
│   └── init_sqlserver.sh        # El arranque de SQL Server, que no carga scripts solo
│
├── backupdb/                    # Respaldos (dumps) — su README explica cómo
│                                #   hacer el backup y cómo restaurarlo
│
├── api_facturas/                # LA API — FastAPI (puerto 8005)
│   ├── Dockerfile               # Su imagen: python:3.12-slim + el driver ODBC
│   ├── requirements.txt         # Las dependencias, con el para qué de cada una
│   ├── main.py                  # Crea la app y registra UN ROUTER POR RECURSO
│   ├── excepciones.py           # ConflictoError: el 409 no tiene builtin razonable
│   ├── controllers/             # Capa 1 — HTTP: 15 archivos, uno por recurso,
│   │                            #   cada uno con su guardia de permisos
│   ├── models/                  # Pydantic: un modelo POR VERBO (POST/PUT/PATCH)
│   │                            #   → de ahí salen los 422
│   ├── servicios/               # Capa 2 — negocio: 15 servicios + el ensamblador
│   │   └── abstracciones/       #   los contratos (typing.Protocol) que ve la capa 1
│   ├── repositorios/            # Capa 3 — datos: 42 implementaciones, TRES por
│   │   └── abstracciones/       #   contrato (PostgreSQL · MariaDB · SQL Server)
│   ├── autorizacion/            # El control de acceso de la v3:
│   │                            #   jwt_token.py (firma y lee) +
│   │                            #   dependencias.py (401 y 403)
│   └── pruebas/                 # prueba_capas.py — el servicio con un repositorio
│                                #   FALSO, sin base de datos
│
├── front_flask/                 # LA INTERFAZ — Flask + Jinja2 (puerto 8046)
│   ├── app.py                   # El ensamblador del front: sesión, menú por permisos
│   ├── cliente_api.py           # El ÚNICO que habla HTTP con la API
│   ├── entidades.py             # El registro: 10 entidades descritas, no copiadas
│   ├── rutas_entidades.py       # Las vistas genéricas que usan ese registro
│   ├── rutas_facturas.py        # La facturación, que NO es un CRUD
│   ├── rutas_usuarios_roles.py  # El usuario con sus roles, con casillas
│   ├── rutas_tablero.py         # Las 10 consultas, pedidas EN PARALELO
│   └── templates/ static/       # Las plantillas y la hoja de marca
│
├── postman/                     # La colección de la API — alternativa a Swagger
│
├── docs/
│   ├── DEMOSTRACION_MOTORES.md  # El cambio de motor, paso a paso y medido
│   ├── spec_kit/                # LAS ESPECIFICACIONES: la constitución permanente
│   │                            #   + una carpeta por versión (v1_sin_fk … v5)
│   │                            #   con sus 9 documentos — 47 en total
│   ├── dominio/                 # 17 documentos del PROYECTO: requisitos, reglas,
│   │                            #   arquitectura, planes por versión, pendientes,
│   │                            #   cronograma, marca y elicitación
│   └── conceptos/               # 25 documentos del CURSO: POO, SOLID, ACID,
│                                #   Docker, async, pruebas, SDD y los tutoriales
│
├── .gitignore / .gitattributes  # Higiene del repo (ignora .venv, EOL)
```

La regla de lectura: **el sistema vive en `docker-compose.yml`**, la API
vive en `api_facturas/` (una carpeta por capa, cada una con su interfaz en
`abstracciones/`), y **todo lo que explica** vive en `docs/`. Cuando lleguen
las versiones siguientes, aquí aparecerán más carpetas de componentes (y el
compose crecerá con ellas). El sistema completo de referencia está en la
rama `sistema-completo`.

## 3. La ruta de versiones

```
v1  sin clave foránea: CRUD de las 6 tablas que no
    dependen de nadie — y la API y su front
v2  con clave foránea: las otras 6, el maestro-detalle
    de la factura por procedimientos, y los puentes
v3  control de acceso: hash, token, 401 y 403
    — el permiso lo resuelve la base de datos
v4  el aplicativo: 10 consultas multitabla, el tablero,
    la marca y la publicación   ← USTED ESTÁ AQUÍ
────────────────────────────────────────────────────────
v5  otros motores: la MISMA API contra MariaDB y
    SQL Server, cambiando una variable   (se PROYECTA)
```

**Cada versión INCLUYE la anterior.** No la reemplaza: la trae adentro, y por
eso en la v4 siguen funcionando los seis recursos de la v1 — y hay una
regresión que lo comprueba.

**Y la v5 está debajo de la raya a propósito:** se proyecta, no se dicta. El
curso cierra en la v4. (En este repositorio los tres motores **ya** están
escritos y medidos, porque es el ejemplo del profesor; eso es la
[demostración](docs/DEMOSTRACION_MOTORES.md), no una versión más.)

> **Ojo con los tags `v2`, `v3` y `v4` de este repositorio:** describen un
> mapa anterior —un motor por versión—. No se mueven, porque un tag es la foto
> de lo que se entregó ese día. Está explicado en
> [`CRONOGRAMA.md`](docs/dominio/CRONOGRAMA.md) §4.

La regla del juego: la **constitución** es permanente, cada versión tiene su
propia spec, y una versión está TERMINADA solo cuando pasa sus criterios de
aceptación. Detalle completo:
**[mapa de versiones](docs/spec_kit/versiones/0_mapa_versiones.md)**.

## 4. Las especificaciones de la versión actual (v4)

| Documento | Qué contiene |
|---|---|
| [Constitución](docs/spec_kit/1_constitution.md) | Las reglas permanentes del proyecto |
| [2_spec.md](docs/spec_kit/versiones/v4_aplicativo/2_spec.md) | QUÉ construir y los 5 criterios de aceptación |
| [3_plan.md](docs/spec_kit/versiones/v4_aplicativo/3_plan.md) | CÓMO: las diez consultas, el tablero y la publicación |
| [4_research.md](docs/spec_kit/versiones/v4_aplicativo/4_research.md) | Las decisiones y sus alternativas descartadas *(lectura opcional)* |
| [5_data_model.md](docs/spec_kit/versiones/v4_aplicativo/5_data_model.md) | Qué tablas cruza cada consulta — sin tablas nuevas |
| [6_contracts.md](docs/spec_kit/versiones/v4_aplicativo/6_contracts.md) | Los endpoints de las consultas y su sobre `{consulta, total, datos}` |
| [7_quickstart.md](docs/spec_kit/versiones/v4_aplicativo/7_quickstart.md) | Arranque, el token y la regresión de las versiones anteriores |
| [8_tasks.md](docs/spec_kit/versiones/v4_aplicativo/8_tasks.md) | Las fases de construcción, en orden |

## 5. Material conceptual del curso

| Documento | Qué cubre |
|---|---|
| [SDD y Spec Kit](docs/conceptos/SDD_SPECKIT.md) | La metodología con la que se trabaja este curso: la spec manda sobre el código |
| [Pruebas y calidad de las pruebas](docs/conceptos/PRUEBAS_Y_CALIDAD_DE_PRUEBAS.md) | Cobertura, la métrica CRAP y mutation testing: cómo saber si sus pruebas de verdad protegen — y por qué hoy es reto opcional, no alcance del proyecto |
| [Programación asincrónica](docs/conceptos/PROGRAMACION_ASINCRONICA.md) | Qué resuelve el async/await en la web, qué se daña sin él (con diagramas), y cómo se ve en el código de este proyecto |
| [El paradigma P.O.O.](docs/conceptos/PARADIGMA_POO.md) | Qué es un paradigma, los 4 pilares, la P.O.O. de Python (`Protocol`, duck typing) y **Pydantic** como clases que validan datos |
| [El flujo de una petición](docs/conceptos/FLUJO_DE_UNA_PETICION.md) | Dónde "está" el GET (el decorador), quién captura el body del POST (Pydantic) y el viaje completo capa por capa — con la pareja PUT/PATCH para probar |
| [Colección de Postman](postman/README.md) | Los 13 endpoints de la v1 listos para importar y probar con clics — incluida la pareja PUT=422 vs PATCH=200 |
| [SOLID, capas y patrones de diseño](docs/conceptos/SOLID_CAPAS_PATRONES.md) | Los 5 principios y las capas — y en qué versión se demuestra cada uno |
| [Principios ACID](docs/conceptos/PRINCIPIOS_ACID.md) | Las 4 garantías transaccionales, por qué una facturación las exige, y el contraste con BASE |
| [Conceptos de Docker](docs/conceptos/CONCEPTOS_DOCKER.md) | Imagen, contenedor, volumen, compose (con el `docker-compose.yml` del proyecto explicado línea por línea) y por qué NO se necesita Kubernetes |
| [Tutorial pgAdmin](docs/conceptos/TUTORIAL_PGADMIN.md) | Administrar la BD paso a paso: conectarse, explorar, editar datos (y verlos cambiar en la API), Query Tool y ERD |
| [Tutorial SQLTools (VS Code)](docs/conceptos/TUTORIAL_VSCODE_SQLTOOLS.md) | La BD sin salir del editor: extensión + driver, conexión, explorar, SELECT/INSERT/DELETE y ejecutar una sentencia entre varias |

---

*Proyecto Paradigmas · USB Med · La rama `sistema-completo` conserva el sistema
de referencia terminado (consultarla es decisión del profesor, no un atajo).*
