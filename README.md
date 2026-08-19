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

```powershell
git clone https://github.com/ccastro2050/proyecto_paradigmas4.git
cd proyecto_paradigmas4
docker compose up -d --build
```

**Eso es todo.** La primera vez tarda unos minutos (descarga imágenes). Al
terminar quedan corriendo la base de datos (bdfacturas completa) y la API:

| Qué | Dónde |
|---|---|
| **API Facturas — Swagger** (probar los endpoints) | http://localhost:8002/docs |
| Diagnóstico | http://localhost:8002/ |
| PostgreSQL (para DBeaver/pgAdmin, opcional) | `localhost:15432` · `paradigmas`/`paradigmas123` |

Pruebe en Swagger: PUT con solo `{"stock": 99}` → 422; el mismo body en
PATCH → 200. Esa diferencia es parte de lo que enseña la v1.

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

> 🤖 **[Guía para construir la versión con IA](docs/GUIA_IA.md)** — los dos
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

> Detalle de todos estos conceptos: [docs/CONCEPTOS_DOCKER.md](docs/CONCEPTOS_DOCKER.md).

---

## 2. Estructura del repositorio

Qué es cada carpeta y cada archivo, y para qué sirve:

```
proyecto_paradigmas4/
├── docker-compose.yml           # TODO el sistema declarado: PostgreSQL + API
│                                #   (el "un solo comando" del proyecto)
├── db/
│   └── init.sql                 # Crea bdfacturas COMPLETA (12 tablas, triggers, datos).
│                                #   PostgreSQL lo ejecuta solo la PRIMERA vez (volumen vacío)
│
├── backupdb/                    # Respaldos (dumps) de la BD — su README explica
│                                #   cómo hacer el backup y cómo restaurarlo
│
├── api_facturas/                # LA API DE LA v1 — FastAPI (puerto 8002)
│   ├── Dockerfile               # Su imagen: python:3.12-slim + requirements
│   ├── requirements.txt         # Dependencias exactas (fastapi, uvicorn, sqlalchemy, asyncpg)
│   ├── main.py                  # Crea la app, configura CORS y registra el router
│   ├── controllers/             # Capa 1 — HTTP: los endpoints de /api/producto
│   ├── models/                  # Pydantic: un modelo por verbo (Producto,
│   │                            #   ProductoReemplazo, ProductoActualizar) → los 422
│   ├── servicios/               # Capa 2 — negocio: servicio + ensamblador (proto-fábrica)
│   │   └── abstracciones/       #   la interfaz (typing.Protocol) que la capa 1 conoce
│   ├── repositorios/            # Capa 3 — datos: SQL asíncrono contra PostgreSQL
│   │   └── abstracciones/       #   la interfaz que la capa 2 conoce
│   └── pruebas/                 # prueba_capas.py — el criterio 6: el servicio
│                                #   con un repositorio FALSO, sin PostgreSQL
│
├── postman/                     # La colección de la API (13 peticiones en orden
│                                #   didáctico) — alternativa a Swagger, con README
│
├── docs/
│   ├── spec_kit/                # LAS ESPECIFICACIONES: constitución permanente +
│   │                            #   una carpeta de specs por versión (v1, v2, …)
│   ├── GUIA_IA.md               # Cómo reconstruir la versión desde 0 con ayuda de una IA
│   ├── FLUJO_DE_UNA_PETICION.md # Dónde "está" el GET y el viaje de una petición por capas
│   ├── PARADIGMA_POO.md         # Material conceptual: POO (con Pydantic), SOLID+capas,
│   ├── SOLID_CAPAS_PATRONES.md         #   ACID, Docker y SDD (un .md por tema)
│   ├── PRINCIPIOS_ACID.md       #
│   ├── CONCEPTOS_DOCKER.md      #
│   ├── SDD_SPECKIT.md           #
│   ├── TUTORIAL_PGADMIN.md      # Tutoriales de administración de la BD, paso a paso
│   ├── TUTORIAL_VSCODE_SQLTOOLS.md  #   con capturas reales
│   └── img_pgadmin/ img_sqltools/   # Las capturas de esos tutoriales
│
├── .gitignore / .gitattributes  # Higiene del repo (ignora .venv, .session.sql, EOL)
└── README.md                    # Este archivo
```

La regla de lectura: **el sistema vive en `docker-compose.yml`**, la API
vive en `api_facturas/` (una carpeta por capa, cada una con su interfaz en
`abstracciones/`), y **todo lo que explica** vive en `docs/`. Cuando lleguen
las versiones siguientes, aquí aparecerán más carpetas de componentes (y el
compose crecerá con ellas). El sistema completo de referencia está en la
rama `sistema-completo`.

## 3. La ruta de versiones

```
v1  api_facturas: CRUD de producto, solo PostgreSQL   (cerrada: tag v1)
v2  más tablas: persona, empresa, cliente, vendedor y
    factura maestro-detalle vía SPs   (cerrada: tag v2)
v3  segundo motor (MariaDB) — nace la fábrica
    y el interruptor DB_PROVIDER   ← USTED ESTÁ AQUÍ
v4  tercer motor (SQL Server) + docker compose completo
v5  API genérica (/api/{tabla})
v6  frontend Flask
```

La regla del juego: la **constitución** es permanente, cada versión tiene su
propia spec, y una versión está TERMINADA solo cuando pasa sus criterios de
aceptación (se cierra con tag). Detalle completo:
**[mapa de versiones](docs/spec_kit/versiones/0_mapa_versiones.md)**.

## 4. Las especificaciones de la versión actual (v3)

| Documento | Qué contiene |
|---|---|
| [Constitución](docs/spec_kit/1_constitution.md) | Las reglas permanentes del proyecto |
| [2_spec.md](docs/spec_kit/versiones/v3_segundo_motor/2_spec.md) | QUÉ construir y los 5 criterios de aceptación |
| [3_plan.md](docs/spec_kit/versiones/v3_segundo_motor/3_plan.md) | CÓMO: la fábrica, los 6 repositorios MariaDB y el interruptor |
| [4_research.md](docs/spec_kit/versiones/v3_segundo_motor/4_research.md) | Las decisiones y sus alternativas descartadas *(lectura opcional)* |
| [5_data_model.md](docs/spec_kit/versiones/v3_segundo_motor/5_data_model.md) | La MISMA bdfacturas en dialecto MariaDB (equivalencias y semillas) |
| [6_contracts.md](docs/spec_kit/versiones/v3_segundo_motor/6_contracts.md) | CERO endpoints nuevos: el mismo contrato con ambos motores |
| [7_quickstart.md](docs/spec_kit/versiones/v3_segundo_motor/7_quickstart.md) | Arranque y la regresión DOBLE (ambos motores) |
| [8_tasks.md](docs/spec_kit/versiones/v3_segundo_motor/8_tasks.md) | Las fases de construcción, en orden |

## 5. Material conceptual del curso

| Documento | Qué cubre |
|---|---|
| [SDD y Spec Kit](docs/SDD_SPECKIT.md) | La metodología con la que se trabaja este curso: la spec manda sobre el código |
| [El paradigma P.O.O.](docs/PARADIGMA_POO.md) | Qué es un paradigma, los 4 pilares, la P.O.O. de Python (`Protocol`, duck typing) y **Pydantic** como clases que validan datos |
| [El flujo de una petición](docs/FLUJO_DE_UNA_PETICION.md) | Dónde "está" el GET (el decorador), quién captura el body del POST (Pydantic) y el viaje completo capa por capa — con la pareja PUT/PATCH para probar |
| [Colección de Postman](postman/README.md) | Los 13 endpoints de la v1 listos para importar y probar con clics — incluida la pareja PUT=422 vs PATCH=200 |
| [SOLID, capas y patrones de diseño](docs/SOLID_CAPAS_PATRONES.md) | Los 5 principios y las capas — y en qué versión se demuestra cada uno |
| [Principios ACID](docs/PRINCIPIOS_ACID.md) | Las 4 garantías transaccionales, por qué una facturación las exige, y el contraste con BASE |
| [Conceptos de Docker](docs/CONCEPTOS_DOCKER.md) | Imagen, contenedor, volumen, compose (con el `docker-compose.yml` del proyecto explicado línea por línea) y por qué NO se necesita Kubernetes |
| [Tutorial pgAdmin](docs/TUTORIAL_PGADMIN.md) | Administrar la BD paso a paso: conectarse, explorar, editar datos (y verlos cambiar en la API), Query Tool y ERD |
| [Tutorial SQLTools (VS Code)](docs/TUTORIAL_VSCODE_SQLTOOLS.md) | La BD sin salir del editor: extensión + driver, conexión, explorar, SELECT/INSERT/DELETE y ejecutar una sentencia entre varias |

---

*Proyecto Paradigmas · USB Med · La rama `sistema-completo` conserva el sistema
de referencia terminado (consultarla es decisión del profesor, no un atajo).*
