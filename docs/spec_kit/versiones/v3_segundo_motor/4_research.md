# Research — Versión 3: decisiones y alternativas

> Lectura opcional: el PORQUÉ de cada decisión del [plan](3_plan.md).

---

## D1 — ¿Fábrica como diccionario, o clases fábrica?

**Alternativas:** (a) el gemelo C# del curso usa el patrón GoF completo
(interfaz `IFabricaRepositorios` + una clase por motor) · (b) un
diccionario `proveedor → {entidad → clase}` con una función.

**Decisión: (b) — el diccionario.** Es el MISMO patrón (una familia
completa por proveedor, un solo punto de decisión) en el idioma de
Python: las clases son objetos de primera categoría y un dict las mapea
sin ceremonia. El costo de agregar motor es idéntico (un bloque) y el
estudiante puede COMPARAR ambas formas del mismo patrón entre gemelos —
eso vale más que la ortodoxia.

## D2 — aiomysql como driver

El driver async estándar de MySQL/MariaDB para SQLAlchemy
(`mysql+aiomysql://`). La alternativa asyncmy es más rápida pero menos
común en documentación — para un curso gana lo canónico. Lección
adicional: cambiar de driver es cambiar el PREFIJO de la cadena; el
repositorio no se entera.

## D3 — OUT + variable de sesión (el CALL en dos pasos)

PostgreSQL devuelve los INOUT como fila del CALL; MariaDB no — el OUT se
recoge con una variable de usuario: `CALL sp(..., @salida)` y luego
`SELECT @salida`. Dos sentencias sobre LA MISMA conexión (la variable
`@salida` vive en la sesión — por eso ambas van dentro del mismo
`engine.begin()`). Es la segunda cara de la misma lección de dialectos
que dio la v2 con P0001.

## D4 — Traducción por código 1644 + patrón de mensaje

MariaDB tampoco numera los errores de negocio como SQL Server: todo
`SIGNAL SQLSTATE '45000'` llega con el código genérico **1644**
(ER_SIGNAL_EXCEPTION). La traducción filtra por ese código y el texto
("no existe" → 404, "anulada" → 409) — el MISMO patrón del repositorio
PostgreSQL con SQLSTATE P0001. Tres motores, tres señales distintas, UNA
frontera que las normaliza.

## D5 — ¿Los dos motores arriba a la vez?

Sí — igual que decidió el gemelo C#: el interruptor solo recrea la API y
comparar motores toma segundos. MariaDB pesa poco (~400 MB de imagen,
~200 MB de RAM); el costo es aceptable y el smoke test §2b lo aprovecha.

## D6 — Motor por defecto: `postgres`

El default conserva el comportamiento de v1/v2 (la regresión corre
idéntica sin tocar nada) y el interruptor muestra el motor nuevo. Es la
decisión opuesta a la del gemelo C# (que estrenó mostrando el motor
nuevo) — deliberadamente: aquí la continuidad pedagógica pesa más porque
el mismo `DB_PROVIDER` será el mecanismo de la API genérica (v5).

## D7 — Puerto 13335

El mapa de puertos del curso ya tiene MariaDB en 13326 (gemelo PHP),
13336 (curso C#) y 13426 (reconstrucción PHP del estudiante). 13335 queda
libre y conserva la forma 133xx. La reconstrucción del estudiante de ESTE
proyecto usa 13435.

## D8 — Semillas idénticas, ids idénticos

`db/init_mariadb.sql` viene del proyecto gemelo PHP (misma BD, otra API)
e inserta los MISMOS datos con los MISMOS ids (`ALTER TABLE …
AUTO_INCREMENT = n` es el `setval` de MariaDB). Consecuencia: el smoke
test corre IGUAL en ambos motores — incluida la nota de la v2 sobre los
autonuméricos consumidos por inserts fallidos (los AUTO_INCREMENT de
InnoDB también avanzan al fallar).
