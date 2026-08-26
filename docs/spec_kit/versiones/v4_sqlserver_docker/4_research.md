# Research — Versión 4: decisiones y alternativas

> Lectura opcional: el PORQUÉ de cada decisión del [plan](3_plan.md).

---

## D1 — aioodbc (y no un driver "puro")

No existe un driver async nativo maduro para SQL Server en Python: el
camino estándar es **aioodbc** (pyodbc async) sobre el driver ODBC 18 de
Microsoft. Costo: la imagen crece (~100 MB) y el Dockerfile aprende a
instalar paquetes de un repositorio APT externo. Beneficio didáctico:
los tres motores muestran tres ecosistemas — Python puro (asyncpg),
wrapper ligero (aiomysql) y puente ODBC (aioodbc).

## D2 — El lote DECLARE/EXEC/SELECT para el OUTPUT

**Alternativas:** (a) pelear con los parámetros OUTPUT de ODBC
(soporte irregular en pyodbc) · (b) un LOTE T-SQL que declara la
variable, ejecuta el SP y la selecciona.

**Decisión: (b)** — es el idioma natural de T-SQL, legible para el
estudiante, y devuelve el JSON como un result set normal. El `SET
NOCOUNT ON` es la trampa clásica documentada en el plan §3.

## D3 — Traducción por patrón de mensaje (sin números)

SQL Server SÍ numera sus THROW (50003, 50010…), pero ODBC entrega el
número INCRUSTADO en el texto, no como código estructurado. En vez de
parsear "(50003)" con regex, el repositorio limpia el prefijo ODBC y
aplica los MISMOS patrones que los otros dos motores ("no existe",
"anulada") — menos frágil y más uniforme entre dialectos. El gemelo C#
sí filtra por número porque SqlClient se lo da estructurado: mismo
problema, mejor herramienta, otra solución — compare.

## D4 — sqlserver-init como contenedor aparte

PostgreSQL y MariaDB ejecutan `/docker-entrypoint-initdb.d/` solos; SQL
Server no tiene ese mecanismo. El inicializador es un contenedor que
espera el healthcheck del motor, corre el script UNA vez (idempotente:
si la BD existe, no hace nada) y muere Exited(0). Es el mismo patrón del
gemelo C# — y la lección de orquestación de la v4: `depends_on` con
`service_completed_successfully`.

## D5 — ¿Y los endpoints de usuario/rol/ruta/puentes?

Las 12 tablas ya viven en los tres motores, pero esta API por-entidad se
queda en sus 6 entidades. **Deliberado:** escribir 5 entidades × 3
dialectos = 15 repositorios más no enseña nada nuevo (el molde ya se
demostró industrial); las entidades restantes se calcarán con el mismo molde
cuando el front (v5) las necesite. (El gemelo C# tomó la decisión opuesta en su v3 — cubrir todo
por-entidad ANTES de cambiar de motor: compare los dos caminos.)

## D6 — Puerto 11435

SQL Server ya tiene 11463 (curso C#) y 11563 (reconstrucción C#). 11435
sigue la forma 114xx y termina en 32 como los demás puertos de esta
familia (15435, 13335). Reconstrucción del estudiante: 11535.

## D7 — RAM: el motor pesado convive con los livianos

SQL Server pide ~2 GB; PostgreSQL ~50 MB; MariaDB ~200 MB. Los tres
quedan SIEMPRE arriba (el interruptor solo recrea la API) — en máquinas
justas, `docker compose stop sqlserver sqlserver-init` libera la RAM
cuando no se está usando ese motor, y `start` lo devuelve.
