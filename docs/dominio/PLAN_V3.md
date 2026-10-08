# Plan de la versión 3 — Facturación (`bdfacturas`)

> **Qué es este documento.** Qué agrega la v3, qué se decidió antes de
> programarla, y **los seis tropiezos que tiene preparados** — cuatro de los
> cuales fallan **en silencio**, y uno de ellos falla **abierto**: concede
> acceso en vez de negarlo, que es lo peor que puede pasarle a un control de
> acceso.
>
> El requisito que manda está en
> [`2_spec.md`](../spec_kit/versiones/v3_control_acceso/2_spec.md). Esto es el
> relato.
>
> **Material académico simulado** en el dominio; los tropiezos son reales, y
> tres de ellos **aparecieron midiendo**, no leyendo.
>
> Versión 1.0 · 7 de octubre de 2026.

---

## 0. Lo que queda al terminar la v3

| Queda | Comprobable con |
|---|---|
| Las cinco tablas que faltaban, con CRUD | `/api/rol` · `/api/ruta` · `/api/usuario` · `/api/rol-usuario` · `/api/rutarol` |
| La contraseña **con hash bcrypt costo 12** | `POST /api/usuario` y después mirar la columna: 60 caracteres que empiezan por `$2b$12$` |
| Un **token firmado** al entrar | `POST /api/sesion/entrar` con `admin@correo.com` / `admin123` |
| **401** sin token y **403** sin permiso | `GET /api/producto` sin cabecera → 401 · con el token de `vendedor1` → 403 |
| El permiso lo decide **la base de datos** | `verificar_acceso_ruta`, llamado en cada petición |
| El front con login y menú por permisos | `localhost:8046` → entra, y el menú cambia según quién sea |

---

## 1. De dónde se partió

Lo que había la mañana del 7 de octubre, medido y no recordado:

| | |
|---|---|
| **En la base de datos** | **Todo.** Las 12 tablas, incluidas `usuario`, `rol`, `ruta` y las dos puente. Y **16 procedimientos**, con `verificar_acceso_ruta`, `crear_usuario_con_roles` y `actualizar_roles_usuario` escritos desde julio |
| **En la API** | **Siete recursos** —producto, persona, empresa, cliente, vendedor, factura y rol— y **ni una línea** de control de acceso: ni token, ni hash, ni 401 |
| **En el front** | El login **escrito y comentado**, con la nota de dónde se volvía a encender |

> **La lección de este punto de partida es la versión entera:** el control de
> acceso ya existía abajo y no existía arriba. No faltaba diseño ni faltaba
> SQL: **faltaba que alguien lo llamara.** Es más común de lo que parece — una
> base de datos bien hecha con una aplicación que no la usa.

---

## 2. La decisión que define la versión: **el permiso NO va en el token**

Un JWT puede llevar lo que uno quiera. Lo cómodo sería meterle la lista de
rutas permitidas al entrar: una consulta por sesión, y después nada.

**No se hizo, y es la decisión que hay que poder defender.**

| | Si el permiso va EN el token | Si se consulta en CADA petición |
|---|---|---|
| **Costo** | Una consulta al entrar | Una consulta por operación |
| **Quitar un permiso** | Surte efecto **cuando el token venza** | Surte efecto **ya** |
| **Tamaño del token** | Crece con los permisos | Fijo |

Y esto no es un argumento teórico: **se midió**. Con un token de `vendedor1`
ya emitido, sin volver a entrar ni una vez:

```
1. vendedor1 pide /api/producto                        403
2. el admin le da al rol Vendedor la ruta /producto
3. el MISMO token pide /api/producto                   200
4. el admin se lo quita
5. el MISMO token pide /api/producto                   403
```

> **Ese 200 del paso 3 es toda la decisión.** Con el permiso dentro del token,
> el paso 3 habría seguido dando 403 —y el paso 5 habría seguido dando 200—
> hasta que la persona volviera a entrar. En un sistema real, «le quité el
> permiso y sigue entrando» es un incidente.

Lo que el token **sí** lleva: el correo (`sub`), los **nombres** de los roles
—para que el menú le hable a una persona— y el vencimiento. Nada más. Y el
motivo es que **un JWT no está cifrado: está firmado**. Cualquiera lo pega en
una página web y lee su contenido; lo que la clave impide es **fabricar** uno.

---

## 3. La segunda decisión: **el permiso lo resuelve la BASE DE DATOS**

La pregunta «¿puede este correo entrar a esta ruta?» cruza tres tablas:

```
usuario → rol_usuario → rol → rutarol → ruta
```

Ese JOIN **no se escribió en Python**. Lo responde `verificar_acceso_ruta`,
que estaba en la base de datos desde el primer día. La razón es de
mantenimiento, no de rendimiento: escribirlo arriba dejaría **la misma regla
en dos sitios**, y el día que cambie uno, el otro miente.

Lo único que la API hace antes de llamarlo es traducir el nombre de la ruta a
su id —el procedimiento recibe el id— y ahí vive una decisión de seguridad
pequeña y fácil de arruinar:

> **Si la ruta no está en la tabla, la respuesta es «no».** Fallar cerrado, no
> abierto. Al contrario, bastaría escribir mal el nombre de una ruta en el
> código para dejar un endpoint sin protección — y nadie lo notaría, porque
> funcionaría.

### Y una tercera decisión: **la guardia va en el router, no en el endpoint**

En .NET esto son dos atributos sobre la clase del controlador; en FastAPI son
**dependencias**:

```python
router = APIRouter(prefix="/api", tags=["Producto"],
                   dependencies=[Depends(exige_permiso("/producto"))])
```

Puesta ahí, corre antes de **cualquier** endpoint del archivo — incluido el
que alguien escriba mañana. Si estuviera endpoint por endpoint, el día que a
alguien se le olvide, ese endpoint queda abierto **y nadie lo nota, porque
funciona**.

Quedan abiertos exactamente dos, y los dos tienen por qué:

| | Por qué no puede exigir token |
|---|---|
| `GET /` | Es el diagnóstico. Un healthcheck que necesita credenciales no sirve de healthcheck |
| `POST /api/sesion/entrar` | Es la puerta de la calle: no puede exigir el token que ella misma entrega |

---

## 4. El orden en que se construyó

| | Qué | Por qué en ese orden |
|---|---|---|
| **1** | `ruta` y `usuario` con sus tres capas | Son el molde de siempre; `usuario` agrega el hash |
| **2** | Los dos puentes | Necesitan que las dos puntas existan |
| **3** | `repositorio_acceso_*` | Llamar al procedimiento que ya estaba |
| **4** | El token y las dos dependencias | Ya había a quién preguntarle |
| **5** | La guardia en los once routers | De golpe, cuando lo demás funcionaba |
| **6** | El front: login, menú y guardias | Lo último, porque sin API no hay nada que probar |

> **Y entre el 4 y el 5 hubo que arreglar algo que no estaba en el plan:** de
> los ocho usuarios sembrados, **solo `admin` podía entrar**. Dos filas tenían
> la contraseña en texto plano y de las otras cinco nadie sabía cuál era —un
> hash no se puede deshacer, y eso es justamente lo que lo hace un hash—. Sin
> poder entrar no se comprueba un solo criterio de esta versión, así que se
> sembraron hash nuevos de claves escritas en el propio script, en los tres
> motores. Está contado en `db/init.sql`.

---

## 5. Los seis tropiezos que esta versión tiene preparados

| | Qué pasa | Por qué cuesta caro |
|---|---|---|
| **1. bcrypt congela la API** | `bcrypt` es **deliberadamente lento** —250 ms con costo 12— y gasta CPU, no espera de red. Llamarlo directo en una función `async` bloquea el bucle de eventos: mientras una contraseña se hashea, **las demás peticiones esperan en fila** | **Falla en silencio**: con un usuario a la vez no se nota nada. Se nota con veinte logins simultáneos, que es cuando ya está en producción. Se arregla con `asyncio.to_thread` |
| **2. `EmailStr` no viene incluido** | El tipo de Pydantic exige el paquete `email-validator`. Sin él, la API **no arranca**: `ImportError` al importar el modelo | Este sí falla a gritos, y es el más fácil. Aquí se resolvió con un patrón de una línea para no arrastrar dos dependencias más |
| **3. El orden de las rutas en FastAPI** | `/api/usuario/verificar-contrasena` encaja también en `/api/usuario/{email}`. FastAPI resuelve **por orden de declaración** | **Falla en silencio**: la petición de verificar acaba buscando un usuario llamado «verificar-contrasena» y devuelve **404**, no un error de programación. La ruta fija se declara ANTES de la ruta con parámetro |
| **4. Un dato malo tumba la API** | `bcrypt.checkpw` **lanza** si el hash guardado está malformado —las dos filas en texto plano—. Sin atraparlo, intentar entrar con ese correo da **500** | Un dato malo en la base de datos no puede tumbar la aplicación: se atrapa y se responde «no coincide» |
| **5. El menú filtrado parece protección** | Esconder «Usuarios» del menú **no protege nada**: es HTML que ya está en el navegador, y quien escriba la dirección entra igual | **Falla en silencio durante meses**: la aplicación «funciona», nadie prueba a escribir la URL, y el día que alguien lo hace ya hay datos de verdad adentro |
| **6. `bool("0")` es `True`** | `verificar_acceso_ruta` devuelve el mismo JSON en los tres motores con el campo `tiene_acceso` de **tres tipos distintos**: booleano en PostgreSQL, número en SQL Server y **cadena** en MariaDB | **Falla ABIERTO y en silencio**: con un `bool()` a secas, ese `"0"` de MariaDB es verdadero y **todo el mundo entra a todo**. Sin excepción, sin registro, con la aplicación «funcionando» |

> **El quinto es el que más se repite en los exámenes**, y por eso la frase
> está escrita en los cuatro sitios donde alguien podría olvidarla: `app.py`,
> `base.html`, `rutas_entidades.py` y el controller de permisos. El menú es
> **comodidad**; la protección es el 403.
>
> **Pero el sexto es el que de verdad da miedo, y apareció midiendo.** Contra
> PostgreSQL todo estaba bien; al cambiar `DB_PROVIDER=mariadb`, `vendedor1`
> entró a `/api/usuario` —justo el 403 que esta versión viene a demostrar—.
> Lo que devuelve cada motor:
>
> ```
> PostgreSQL   {"tiene_acceso": false}     booleano
> SQL Server   {"tiene_acceso": 0}         número
> MariaDB      {"tiene_acceso": "0"}       CADENA
> ```
>
> Se arregla con una conversión explícita en cada repositorio —la capa que
> conoce su motor— que **lista los valores que acepta** y devuelve `False`
> ante cualquier otra cosa: fallar cerrado, no abierto. Y está en los tres,
> incluido el de PostgreSQL donde no hace falta, para que nadie lo
> «simplifique» y copie el atajo al que sí rompe.
>
> **La moraleja no es sobre JSON: es sobre probar contra los tres motores.**
> Dos de los tres funcionaban por casualidad.

---

## 6. Cómo se verificó

No se leyó: se corrió, con la API arriba.

```powershell
# 1. sin token
Invoke-RestMethod http://localhost:8005/api/producto          # 401

# 2. entrar
$s = Invoke-RestMethod -Method Post http://localhost:8005/api/sesion/entrar `
      -ContentType 'application/json' `
      -Body '{"email":"vendedor1@correo.com","contrasena":"vendedor123"}'

# 3. con token, donde SÍ tiene permiso
Invoke-RestMethod http://localhost:8005/api/factura `
      -Headers @{ Authorization = "Bearer $($s.token)" }     # 200

# 4. con token, donde NO
Invoke-RestMethod http://localhost:8005/api/usuario `
      -Headers @{ Authorization = "Bearer $($s.token)" }     # 403
```

La matriz completa, medida con los tres usuarios:

| | `/producto` | `/factura` | `/cliente` | `/usuario` | `/permiso` |
|---|---|---|---|---|---|
| **admin** | 200 | 200 | 200 | 200 | 200 |
| **vendedor1** | 403 | 200 | 200 | 403 | 403 |
| **cliente1** | 200 | 403 | 403 | 403 | 403 |

Y la misma matriz **en los tres motores**, que es lo que descubrió el sexto
tropiezo. Con `DB_PROVIDER` en cada valor y los tres usuarios:

| | admin | vendedor1 | cliente1 |
|---|---|---|---|
| **postgres** | 200 · 200 · 200 | 403 · 200 · 403 | 200 · 403 · 403 |
| **mariadb** | 200 · 200 · 200 | 403 · 200 · 403 | 200 · 403 · 403 |
| **sqlserver** | 200 · 200 · 200 | 403 · 200 · 403 | 200 · 403 · 403 |

*(las tres rutas de cada celda: `/api/producto`, `/api/factura`, `/api/usuario`)*

En el front, las mismas tres sesiones: `admin` ve 14 enlaces, `vendedor1`
cuatro, `cliente1` tres — y las rutas sin permiso responden 302 al inicio con
el mensaje, en vez de dejar ver una pantalla que la API va a rechazar.

---

## 7. Lo que queda para la v4

| | |
|---|---|
| **Las diez consultas** | Ninguna pregunta cruza todavía cuatro tablas para un reporte |
| **El tablero** | La página que las muestra todas |
| **`usuario-con-roles`** | El usuario y sus roles en un solo envío, por procedimiento |

> **Y lo que la v4 NO va a traer:** otro motor. Esa es la v5, y se proyecta —
> no se dicta ([`0_mapa_versiones.md`](../spec_kit/versiones/0_mapa_versiones.md)).
