# Lo que falta — registro de pendientes

> **Qué es este documento.** Lo que este repositorio **todavía no tiene**,
> dicho antes de que alguien lo descubra en clase. Cada punto dice **qué
> falta**, **cuánto** y **cómo se comprueba** que ya se hizo.
>
> No es una lista de deseos: es lo que se midió el **7 de octubre de 2026**.
>
> **La regla de este archivo:** un pendiente que se cierra se **tacha con su
> commit**, no se borra. Lo que se borró nunca estuvo — y un documento donde
> los pendientes desaparecen sin rastro no se puede auditar.

---

## 1. Lo que estaba pendiente y ya no lo está

**Todas las v4 de la ruta son equivalentes; lo único que cambia es el stack.**
Aquí el stack es **FastAPI + Flask + PostgreSQL**. Esta tabla es la que por la
mañana decía qué faltaba, con lo que pasó el mismo día:

| | Lo que exige la versión | Estado |
|---|---|---|
| ~~**CRUD de las 12 tablas**~~ | 12 recursos en la API | ~~7 de 12~~ → **cerrado** (`9a6efff`): entraron ruta, usuario, rutarol y rol_usuario |
| ~~**Control de acceso**~~ | hash, token, 401 y 403 | ~~nada en Python~~ → **cerrado** (`57e5cb3`): token, las dos dependencias y los 403 medidos |
| ~~**10 consultas multitabla**~~ | con su tablero | ~~nada~~ → **cerrado** (`dabf06b`): diez rutas declaradas y el tablero dibujando |
| ~~**El front**~~ | todas las pantallas | ~~6 entidades + facturas~~ → **cerrado** (`2e322f8`): 14 pantallas, una por recurso |

> ### Y lo que ya estaba completo desde el principio
>
> **La base de datos no era el problema.** `db/init.sql` ya traía las **12
> tablas**, el **disparador** de totales y stock, y **16 procedimientos** —
> incluidos `verificar_acceso_ruta`, `crear_usuario_con_roles` y
> `actualizar_roles_usuario`.
>
> El control de acceso **existía en la base de datos** desde el primer día;
> lo que no existía era el código Python que lo llamara. **El hueco estaba
> arriba, no abajo** — y eso es lo que esta versión vino a enseñar.

---

## 2. Lo que SÍ sigue pendiente

Tres cosas, y conviene decirlas con el mismo detalle que las cerradas:

| Qué | Por qué está así | Cómo se cerraría |
|---|---|---|
| **El token no se puede retirar** | Un JWT es autocontenido: `DELETE /api/sesion` le dice al cliente que lo borre, pero el token sigue siendo válido hasta que vence. Es la contrapartida de no guardar estado, y el propio endpoint lo dice en su respuesta | Una lista negra en la base de datos y una consulta por petición — justo lo que un JWT viene a evitar. Mientras tanto, la defensa es que dure poco (`JWT_MINUTOS`) |
| **`JWT_CLAVE` tiene valor por omisión** | Para que el aula arranque con un solo comando. En un sistema de verdad, la API debería **negarse a arrancar** sin esa variable | Quitar el valor por omisión de `autorizacion/jwt_token.py` y fallar al iniciar |
| **Los tags `v2`, `v3` y `v4` describen el mapa viejo** | «segundo motor», «tercer motor». Con el mapa nuevo esas serían la v5 | **No se tocan.** Un tag es la foto de lo que se entregó ese día; reescribirlo sería falsificar la historia ([`CRONOGRAMA.md`](CRONOGRAMA.md) §4) |

### Dos cosas que parecen pendientes y no lo son

| Qué | Por qué está bien así |
|---|---|
| **`productos-sin-vender` e `interfaces-sin-usuarios` devuelven vacío** | Porque **es el dato correcto**: con los datos sembrados, todo producto se ha vendido alguna vez y toda ruta tiene quien entre. Una consulta que devuelve cero filas no está rota — y confundir «vacío» con «falla» hace perder tardes enteras |
| **`DELETE /api/usuario` puede dar 500** | Si el usuario todavía tiene roles, la foránea de `rol_usuario` rechaza el borrado. No es un defecto: es la base de datos protegiendo su integridad. Para borrar usuario **y** roles de una vez está `DELETE /api/usuario-con-roles/{email}`, que llama al procedimiento que hace las dos cosas en una transacción |

---

## 3. Documentos que NO están, y por qué

De los dieciocho del dominio, uno **no se escribió a propósito**, porque
escribirlo sería inventar:

| Documento | Por qué no está |
|---|---|
| **`PLAN_DE_TRABAJO.md`** | En los otros repositorios es el acta donde **tres estudiantes** acuerdan el reparto. Aquí hay **un solo autor** ([`CRONOGRAMA.md`](CRONOGRAMA.md) §1): no hay equipo que simular, y un acta de una sola persona es un adorno |

> **`PLAN_V3` y `PLAN_V4` sí están**, y antes no: no se escribieron hasta que
> esas versiones se construyeron. Un plan de algo que no existe es ficción —
> y cuando el código llegó, el plan se pudo escribir con lo que de verdad
> costó cada decisión.

---

## 4. Las guías de IA

| | |
|---|---|
| **Por versión** | **Las cinco están**: `GUIA_IA1` … `GUIA_IA5`, una por carpeta del spec kit. Más la general de `docs/conceptos/GUIA_IA.md`, que explica el método |
| **Por estudiante** | Los otros repositorios traen **quince** —Carlos, Paco y Luis, una por versión—. Aquí **ninguna**, y es coherente: un solo autor |

---

## 5. Cómo se midió todo esto

Para que el próximo no tenga que creer:

| Qué se comprobó | Con qué |
|---|---|
| Los 15 controllers de la API | `ls api_facturas/controllers/*_controller.py` |
| Las 45 rutas y 85 operaciones | `curl -s localhost:8005/openapi.json` y contarlas |
| Que el control de acceso funciona | Entrar como `admin`, `vendedor1` y `cliente1` y pedir cinco rutas con cada token: 200 y 403 donde toca |
| Que el permiso NO está en el token | Con un token ya emitido: 403 → el admin concede la ruta → **200 sin volver a entrar** → el admin la quita → 403 |
| Que la base SÍ tenía los procedimientos | `grep -c 'CREATE OR REPLACE PROCEDURE' db/init.sql` → **16** |
| Que los tres motores responden igual | `DB_PROVIDER` en los tres valores: `GET /api/producto` → 200 y los mismos ocho productos |
| Que el front funciona | Las 14 pantallas responden 200 con sesión de admin; 302 al inicio con la de `vendedor1` donde no tiene permiso |

---

| Qué | Dónde |
|---|---|
| El mapa nuevo, y por qué la v5 está fuera | [`0_mapa_versiones.md`](../spec_kit/versiones/0_mapa_versiones.md) |
| Lo que costó el control de acceso | [`PLAN_V3.md`](PLAN_V3.md) |
| Lo que costó el aplicativo y el tablero | [`PLAN_V4.md`](PLAN_V4.md) |
| La historia real, contada de `git log` | [`CRONOGRAMA.md`](CRONOGRAMA.md) |
| De dónde salió cada cosa | [`FUENTES.md`](FUENTES.md) |
| El cambio de motor, paso a paso | [`DEMOSTRACION_MOTORES.md`](../DEMOSTRACION_MOTORES.md) |
