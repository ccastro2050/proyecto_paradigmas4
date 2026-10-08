# Research — Versión 5: decisiones y alternativas

> Lectura opcional: el PORQUÉ de cada decisión del [plan](3_plan.md).

---

## D1 — ¿Fábrica abstracta, o un `switch` en cada registro?

**Alternativas:** (a) un `switch (motor)` dentro de cada uno de los 11
`AddScoped` · (b) inyección con llaves de .NET (keyed services) · (c) una
**fábrica abstracta**: interfaz con 11 métodos, una implementación por
motor.

**Decisión: (c).** Con (a), la decisión del motor se repite 11 veces (y
con un tercer motor serían 33 ramas). Con (b), la magia del contenedor esconde el
patrón que el curso quiere ENSEÑAR. La fábrica es el patrón clásico GoF
visible en dos archivos leíbles: agregarle un motor = una clase + un
case. El costo (11 métodos "aburridos" en la interfaz) ES la lección: la
fábrica promete la familia COMPLETA de repositorios, no uno suelto.
(El documento [SOLID, capas y patrones](../../../conceptos/SOLID_CAPAS_PATRONES.md)
lo anunciaba — hoy se cumple.)

## D2 — SQLAlchemy como cliente

Es el cliente ADO.NET oficial de MariaDB, con las MISMAS clases
conceptuales (`SQLAlchemyConnection`/`Command`/`DataReader`) que ya se dominan
de SQLAlchemy. La traducción de 13 de los 14 repositorios queda mecánica —
eso también es didáctico: el conocimiento de ADO.NET se transfiere entre
motores.

## D3 — SPs con `CommandType.StoredProcedure` + parámetro OUTPUT

**Alternativas:** (a) un lote de texto `DECLARE/EXEC/SELECT` ·
(b) `CommandType.StoredProcedure` con `@p_resultado OUTPUT`.

**Decisión: (b)** en PostgreSQL, que es el idioma nativo de SqlClient: los
parámetros OUTPUT son de primera clase. Matiz técnico: el tamaño del
parámetro va en `-1` (= `NVARCHAR(MAX)`).

**En MariaDB no hay parámetro OUTPUT**: el `CALL` de un procedimiento con
`INOUT` devuelve una FILA con ese valor, así que SQLAlchemy lo lee como un
resultado normal. Es la misma idea con otra mecánica.

## D4 — Traducir errores por NÚMERO (el contraste con P0001)

En la v2 el curso aprendió a traducir los `THROW` de PostgreSQL por NÚMERO:
`THROW 50003` (consultar: no existe) y `THROW 50010` (anular: no existe / ya
anulada) llegan en `SqlException.Number`, y el número es inequívoco.

**MariaDB no numera los errores de negocio.** Un `RAISE EXCEPTION` llega
siempre con SQLSTATE `P0001`, así que hay que filtrar por SQLSTATE + patrón
del mensaje. El filtro por número + patrón es MÁS
preciso — misma frontera, mejor señal. Dos motores, dos maneras de
avisar, UNA traducción por dialecto en su repositorio.

## D5 — ¿Los dos motores arriba a la vez, o perfiles de compose?

**Decisión: ambos siempre arriba.** El interruptor solo recrea la API —
comparar motores toma segundos y el smoke test §2 lo aprovecha. El costo
es RAM (~2 GB de MariaDB + ~50 MB de Postgres — la asimetría también
enseña). En máquinas justas: `docker compose stop mariadb
mariadb-init` libera el motor pesado y `start` lo devuelve.

## D6 — Motor por defecto: `postgres`

El default conserva el comportamiento de v1-v4 (la regresión corre
idéntica sin tocar nada) y el interruptor estrena el motor nuevo. El
default vive en el compose (`${DB_PROVIDER:-postgres}`), no en el código.

## D7 — Puerto 13335

Mapa de puertos: la familia de este curso termina en 42 (API 8005,
PostgreSQL 15435) — MariaDB toma **13335** (libre entre los 114xx ya
usados por otros cursos: 11463, 11563, 11432). La reconstrucción del
estudiante suma 100: **15562**.

## D8 — Semillas idénticas, ids idénticos

`db/bdfacturas_mariadb.sql` inserta los MISMOS datos con los MISMOS
ids (con `SET SERIAL_INSERT` — el `setval` de MariaDB).
Consecuencia valiosa: el smoke test de v1-v4 corre IGUAL en ambos
motores — hasta la nota del quickstart v3 sobre los ids consumidos por
inserts fallidos aplica igual (los SERIAL también avanzan al fallar).
