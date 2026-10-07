# Mapa de versiones — Proyecto Paradigmas

> **Cómo se trabaja este proyecto: por versiones** (desarrollo incremental
> guiado por especificaciones). La **constitución es permanente**
> ([../1_constitution.md](../1_constitution.md)) y cada versión tiene **su
> propia especificación, plan y tareas** en una carpeta `vN_nombre/`.
>
> **El stack es el mismo en las cuatro versiones del curso:**
>
> | | |
> |---|---|
> | **La API** | **Python + FastAPI** |
> | **El front** | **Python + Flask** (Jinja2) |
> | **La base de datos** | **PostgreSQL**, y solo PostgreSQL |
>
> Versión 2.0 · 7 de octubre de 2026.

---

## Lo primero: estas versiones son LAS MISMAS en los cinco cursos

**Todas las v4 de la ruta son equivalentes. Lo único que cambia es el stack.**

| Curso | API | Front | Base de datos |
|---|---|---|---|
| Aplicación y Servicios Web (ITM) | .NET | Blazor | SQL Server |
| Construcción de Software (USB) | .NET | Blazor | PostgreSQL |
| Diseño de Software (USB) | .NET | Flask | PostgreSQL |
| **Paradigmas (USB) — este** | **FastAPI** | **Flask** | **PostgreSQL** |
| PHP (ITM) | PHP | PHP | MariaDB |

> **Lo que se entrega es idéntico**: las mismas tablas, los mismos
> procedimientos, las mismas consultas y el mismo tablero. Cambia el lenguaje
> con que se escribe, no lo que hay que construir — y por eso un estudiante
> puede mirar el repositorio de otro curso y entenderlo.

---

## Las CUATRO versiones del curso

| Versión | Qué agrega (acumulativo) | Estado |
|---|---|---|
| **v1** | CRUD completo de **las seis tablas sin clave foránea** — **API e interfaz gráfica** | — |
| **v2** | CRUD de **TODAS las tablas**: con la v2 están las 12. Las claves foráneas como **listas desplegables cargadas de la API**, las **tablas puente**, y la **factura maestro-detalle** por procedimientos | — |
| **v3** | **El control de acceso**: la contraseña con hash, la sesión con token, y el permiso resuelto en la base de datos. **No agrega tablas**: le pone la puerta a lo que ya existe | — |
| **v4** | **El aplicativo**: 10 consultas multitabla (4+ tablas cada una), tablero con gráficos, imagen corporativa con su manual de marca, responsive y **publicación** | — |

> **Cada versión entrega su parte de la API *y* su parte del front.** Media
> versión no es una versión: si la API responde y la interfaz no, la versión no
> está cerrada.
>
> **Y son acumulativas.** La v2 contiene la v1, la v3 contiene la v2. De ahí la
> **regresión**: los criterios de las versiones anteriores se vuelven a correr
> el día de la entrega.

---

## Y una v5, que está FUERA de las cuatro del curso

| Versión | Qué agrega | Estado |
|---|---|---|
| **v5** | **Otros motores de base de datos**: la misma API contra **MariaDB** y **SQL Server**, con el interruptor `DB_PROVIDER` que elige cuál atiende | **Adelantada** — ver abajo |

**Por qué está fuera de las cuatro, y no es un desprecio:**

| | |
|---|---|
| **El curso son cuatro** | El calendario del semestre está armado sobre esas cuatro |
| **No agrega funcionalidad** | Cambiar de motor agrega **otra implementación de la misma interfaz**. Quien usa el sistema no nota nada |
| **Y aun así vale la pena** | Es **la prueba** de que la abstracción del repositorio servía: se agrega un motor **sin tocar el servicio ni el controlador** |

> **Es la única versión cuyo criterio de éxito es que NO haya que cambiar
> nada.** En las otras cuatro, terminar significa que algo nuevo funciona; en
> la v5, que lo viejo **siguió** funcionando con otro motor debajo.

---

## La v5 ya está construida en este repositorio

Y conviene decirlo sin rodeos, porque explica lo que se ve al levantar el
sistema: **el `docker-compose.yml` enciende tres motores**, no uno.

| | |
|---|---|
| **Qué está hecho** | Los repositorios contra **PostgreSQL**, **MariaDB** y **SQL Server**, y el interruptor `DB_PROVIDER` que elige cuál atiende **sin recompilar** |
| **Qué demuestra** | Comprobado el 7 de octubre de 2026: con `DB_PROVIDER` en los tres valores, `GET /api/producto` responde **200** y **los mismos ocho productos**, con el mismo sobre `{tabla, limite, total, datos}` |
| **Por qué está adelantada** | Porque se construyó antes de que el mapa cambiara, y era código que funcionaba. Tirarlo habría sido peor que explicarlo |

> **Lo que NO hay que concluir de eso:** que el curso vaya de motores. Las
> versiones 1 a 4 son **PostgreSQL y nada más**. Los otros dos están ahí como
> adelanto, y el estudiante no tiene que tocarlos para entregar su v4.

---

## Lo que falta para que este repositorio tenga su v4

Dicho con números, para que nadie se sorprenda:

| | Lo que exige la versión | Lo que hay hoy |
|---|---|---|
| **v1–v2** | CRUD de **las 12 tablas** | **6**: producto, persona, empresa, cliente, vendedor y factura |
| **v2** | El front con sus pantallas | **No existe el front** |
| **v3** | Hash, token y permiso por ruta | **Nada** |
| **v4** | 10 consultas multitabla y el tablero | **Nada** |

---

## Las reglas del trabajo por versiones

1. **La constitución no se toca entre versiones.** Si una versión exige cambiar
   una regla de la constitución, es una decisión mayor que se discute aparte.
2. **Cada carpeta de versión es autocontenida**: con la constitución más esa
   carpeta se puede construir la versión desde el estado anterior.
3. **El código de una versión no anticipa a la siguiente.** En la v1 no se
   escribe la fábrica multi-motor «por si acaso»: se escribe la interfaz, y la
   fábrica llega cuando un segundo motor la justifique. **YAGNI con
   dirección** — no se escribe hoy lo que solo hará falta mañana, pero se sabe
   hacia dónde va.
4. **Cada versión termina en verde**: criterios verificables, commit y tag.
5. **La spec de la siguiente parte del estado real** dejado por la anterior. Si
   el código divergió de la spec, primero se reconcilia: la spec siempre
   refleja el estado actual.
