# Lo que falta — registro de pendientes

> **Qué es este documento.** Lo que este repositorio **todavía no tiene**,
> dicho antes de que alguien lo descubra en clase. Cada punto dice **qué
> falta**, **cuánto** y **cómo se comprueba** que ya se hizo.
>
> No es una lista de deseos: es lo que se midió el **7 de octubre de 2026**.
>
> **La regla de este archivo:** un pendiente que se cierra se **tacha con su
> commit**, no se borra. Lo que se borró nunca estuvo.

---

## 1. La distancia entre lo que hay y una v4

**Todas las v4 de la ruta son equivalentes; lo único que cambia es el stack.**
Aquí el stack es **FastAPI + Flask + PostgreSQL**. Y esto es lo que falta para
que esta v4 sea la misma que las otras:

| | Lo que exige la versión | Lo que hay hoy | Falta |
|---|---|---|---|
| **CRUD de las 12 tablas** | 12 recursos en la API | **7**: producto, persona, empresa, cliente, vendedor, factura y rol | **5**: ruta, usuario, rol_usuario, rutarol y usuario-con-roles |
| **Control de acceso** | hash, token, 401 y 403 | **nada en Python** | todo el código |
| **10 consultas multitabla** | con su tablero | **nada** | las diez y la pantalla |
| **El front** | todas las pantallas | **6 entidades + facturas** | las que falten cuando la API crezca |

> ### Y una cosa que SÍ está completa, y conviene saberlo
>
> **La base de datos no es el problema.** `db/init.sql` ya trae las **12
> tablas**, el **disparador** de totales y stock, y **16 procedimientos** —
> incluidos `verificar_acceso_ruta`, `crear_usuario_con_roles` y
> `actualizar_roles_usuario`.
>
> O sea: **el control de acceso ya existe en la base de datos**; lo que no
> existe es el código Python que lo llame. El hueco está arriba, no abajo.

---

## 2. El mapa de versiones y los tags

| | Qué pasa |
|---|---|
| **Los tags `v2`, `v3` y `v4`** | Describen el mapa **viejo** —un motor por versión—. Con el mapa nuevo, «segundo motor» y «tercer motor» son la **v5** |
| **Las carpetas del spec kit** | Se llaman `v1_producto_postgres`, `v2_mas_tablas`, `v3_segundo_motor`, `v4_sqlserver_docker`. En los otros repositorios son `v1_sin_fk` … `v5_otros_motores` |
| **Qué habría que hacer** | Renombrarlas y reescribir lo que cada una especifica. Y decidir qué pasa con los tags, que quedarían describiendo otra cosa |

---

## 3. Documentos que NO están, y por qué

Tres de los dieciocho del dominio **no se escribieron a propósito**, porque
escribirlos sería inventar:

| Documento | Por qué no está |
|---|---|
| **`PLAN_V3.md`** | La v3 del mapa nuevo —el control de acceso— **no se ha construido**. Un plan de algo que no existe es ficción |
| **`PLAN_V4.md`** | Igual: las diez consultas y el tablero no están |
| **`PLAN_DE_TRABAJO.md`** | En los otros repositorios es el acta donde **tres estudiantes** acuerdan el reparto. Aquí hay **un solo autor** ([`CRONOGRAMA.md`](CRONOGRAMA.md) §1): no hay equipo que simular |

> **Se escriben cuando haya qué contar.** `PLAN_V1` y `PLAN_V2` sí están,
> porque esas versiones sí se construyeron.

---

## 4. Las guías de IA

| | |
|---|---|
| **Por versión** | En los otros repositorios cada carpeta de versión trae su `GUIA_IA<N>.md`. Aquí hay **una sola**, suelta, en `docs/conceptos/GUIA_IA.md` |
| **Por estudiante** | Los otros traen **quince** —Carlos, Paco y Luis, una por versión—. Aquí **ninguna**, y es coherente: no hay equipo simulado |

---

## 5. Cómo se midió todo esto

Para que el próximo no tenga que creer:

| Qué se comprobó | Con qué |
|---|---|
| Los siete recursos de la API | `ls api_facturas/controllers/*_controller.py` |
| Que no hay control de acceso | Buscar `jwt`, `token` o `Depends` de autenticación en `api_facturas/`: cero |
| Que la base SÍ los tiene | `grep -c 'CREATE OR REPLACE PROCEDURE' db/init.sql` → **16** |
| Que los tres motores responden igual | `DB_PROVIDER` en los tres valores: `GET /api/producto` → 200 y los mismos ocho productos |
| Que el front funciona | Las siete pantallas responden 200 con datos reales |

---

| Qué | Dónde |
|---|---|
| El mapa nuevo, y por qué la v5 está fuera | [`0_mapa_versiones.md`](../spec_kit/versiones/0_mapa_versiones.md) |
| La historia real, contada de `git log` | [`CRONOGRAMA.md`](CRONOGRAMA.md) |
| De dónde salió cada cosa | [`FUENTES.md`](FUENTES.md) |
| El cambio de motor, paso a paso | [`DEMOSTRACION_MOTORES.md`](../DEMOSTRACION_MOTORES.md) |
