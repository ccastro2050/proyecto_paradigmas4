# Plan técnico — Versión 3: el control de acceso

> | | |
> |---|---|
> | **Qué hay que construir** | [2_spec.md](2_spec.md) |
> | **Los formatos exactos** | [6_contracts.md](6_contracts.md) |
> | **El orden** | [8_tasks.md](8_tasks.md) |
> | **Los conceptos** | [CONCEPTOS_CONTROL_DE_ACCESO.md](../../../conceptos/CONCEPTOS_CONTROL_DE_ACCESO.md) |

---

## 1. Lo único que se agrega a la pila

| Paquete | Para qué |
|---|---|
| **`pyjwt`** | Firma y valida el token en cada petición |
| **`passlib[bcrypt]`** | El hash de la contraseña, con su sal |
| **`python-multipart`** | Para que FastAPI lea el formulario de entrada |

**Y las versiones no se adivinan:** se fijan en `requirements.txt` con el
número exacto que ya corre, y se copian de un proyecto que arranca. Elegir
un número por intuición es lo que hace perder una tarde.

> **Lo que NO se agrega:** ninguna librería de «autorización». El permiso ya
> está resuelto en la base de datos —el procedimiento `verificar_acceso_ruta`
> existe desde el primer día— y lo que falta es llamarlo.

> **`bcrypt` ya estaba** desde antes, y el hash de la contraseña **ya
> funcionaba**. Lo que faltaba no era el hash: era la **puerta**.

## 2. Las tres piezas, y por qué son tres

```
   credenciales          token            permiso
        │                  │                 │
   AUTENTICA ────────►  SESIÓN  ────────► AUTORIZA
   ¿quién es?         (lo recuerda)       ¿puede esto?
        │                  │                 │
  ServicioSesion      JwtBearer        ExigePermiso
   + BCrypt           (middleware)   + verificar_acceso_ruta
```

| | Archivo | Qué resuelve |
|---|---|---|
| **1** | `servicios/servicio_sesion.py` | Compara el hash y **arma** el token |
| **2** | `main.py` → `AddJwtBearer` | **Valida** el token en cada petición. **401** si no sirve |
| **3** | `autorizacion/guardia_permisos.py` | Pregunta el permiso. **403** si el rol no puede |

> **Sin la 1 las otras dos no tienen a quién validar. Sin la 2, la 3 no sabe
> quién pregunta. Y sin la 3, el sistema sabe quién entra y le deja hacer todo.**
> El orden no es un gusto: cada una necesita la anterior.

## 3. Los archivos nuevos

### 3.1 La sesión

```
models/configuracion_jwt.py       los 4 valores con los que se firma y se valida
models/sesion.py                 lo que recibe quien se identifica
models/sesion_crear.py         { email, contrasena }  ← EN EL CUERPO
servicios/i_servicio_sesion.py
servicios/servicio_sesion.py       compara el hash y arma el token
controllers/sesion_controller.py   POST /api/sesion/entrar — el único [AllowAnonymous]
```

**Dos decisiones de diseño que vale la pena leer dos veces:**

| | |
|---|---|
| **Las credenciales van en el CUERPO** | El endpoint de la versión anterior las recibía por la URL: `?valor_usuario=…&valor_contrasena=…`. **Una contraseña en la URL queda en el historial del navegador y en los logs de cualquier proxy del camino.** Ese endpoint se queda —no se toca lo cerrado— y el inicio de sesión de verdad usa el cuerpo |
| **El mismo error para los dos casos** | Correo inexistente y contraseña equivocada responden **lo mismo**. Decir «ese correo no existe» le confirma a un desconocido **cuáles sí existen** — y con una lista de correos válidos, probar contraseñas vale la pena |

### 3.2 El permiso

```
repositorios/i_repositorio_acceso.py
repositorios/repositorio_acceso_postgres.py   llama verificar_acceso_ruta
autorizacion/guardia_permisos.py       el filtro que responde 403
controllers/permisos_controller.py           GET /api/permisos/mios, para el menú
```

**La guardia, que es la pieza central:**

```python
from autorizacion.dependencias import exige_permiso

router = APIRouter(prefix="/api", tags=["Usuario"],
                   dependencies=[Depends(exige_permiso("/usuario"))])
#                                        ^ exige TOKEN    -> 401
#                                          y PERMISO      -> 403
```

> **Una sola dependencia hace las dos cosas**, y no es por ahorrar: por dentro,
> `exige_permiso` depende de `usuario_actual`, y FastAPI resuelve esa cadena
> antes de entrar al endpoint. Si el token falta o no sirve, `usuario_actual`
> responde 401 y el permiso nunca se consulta. En el gemelo .NET son dos
> atributos —`[Authorize]` y `[ExigePermiso]`— porque allá el marco los
> encadena por fuera.

| | Por qué así |
|---|---|
| **Va en el ROUTER, no en cada endpoint** | Si fuera una línea dentro de cada función, el día que alguien escriba un endpoint nuevo y se le olvide, **ese endpoint queda abierto** — y nadie lo nota, porque funciona |
| **Se consulta EN CADA PETICIÓN** | Es más trabajo —una consulta por operación— y es lo que hace que **quitarle un permiso surta efecto sin volver a identificarse** |
| **El nombre de la ruta sale de la tabla `ruta`** | `/usuario`, `/factura`… son los valores que la base de datos ya trae sembrados. No se inventan |

### 3.3 La interfaz gráfica

```
app.py                      la sesión, el menú por permisos y login_requerido
cliente_api.py              iniciar_sesion() y mis_permisos(); pone la cabecera
templates/login.html        la pantalla de identificación
templates/base.html         el menú ARMADO CON LOS PERMISOS, y quién está dentro
```

**Y nada más.** Son dos archivos de Python y dos plantillas: el front no gana
una capa por tener sesión, porque `cliente_api.py` ya era el único que habla
HTTP y ahí es donde entra la cabecera.

## 4. Las cuatro decisiones del front, con su razón

### 4.1 El token vive en la COOKIE DE SESIÓN de Flask, no en `localStorage`

```python
app.secret_key = os.environ.get("CLAVE_SESION", "clave-solo-para-desarrollo")
session["token"] = sesion["token"]
```

| | |
|---|---|
| **Qué se gana** | Flask **firma** esa cookie con `secret_key`: el navegador no la puede alterar sin romper la firma. Y sobrevive al F5, porque no depende de ninguna conexión abierta |
| **Qué se pierde, y hay que decirlo** | La cookie **sí baja al navegador**. No es `HttpOnly` por arte de magia —Flask la marca así, y eso impide que la lea un script, pero sigue viajando en cada petición |

> **Lo que NO se hace es `localStorage`**, que es la tentación: ahí cualquier
> script de la página lo puede leer, y basta una dependencia comprometida para
> que el token se vaya a otro servidor.
>
> **Y la clave que firma la cookie sale del entorno**, no del código: una clave
> escrita en el repositorio es una clave publicada.

### 4.2 La cabecera se pone en UN solo archivo

```python
def _cabecera(token=None):
    if token is None:
        token = session.get("token")
    return {"Authorization": f"Bearer {token}"} if token else {}
```

Todas las funciones de `cliente_api.py` la usan. **Y si no hay token, se manda
sin ella** —y la API responde 401, que es lo correcto: el front no simula una
sesión que no existe.

> **Por qué no un envoltorio automático** sobre `requests`: porque el front
> tiene **un** cliente y una función de cabecera; agregar una capa de sesión de
> `requests` para ahorrar una línea escondería dónde se pone el token, que es
> justo lo que hay que poder mostrar en clase.

### 4.3 El tablero lee el token ANTES de abrir los hilos

Las diez consultas de la v4 se piden en paralelo, y ahí aparece algo que
sorprende:

```python
token = session.get("token")        # en el hilo de la petición
with ThreadPoolExecutor(...) as grupo:
    grupo.map(pedir, CONSULTAS)     # y viaja como ARGUMENTO
```

`session` pertenece al contexto de la petición de Flask, y **un hilo nuevo no
lo tiene**. El camino que no sirvió —envolver con
`copy_current_request_context`— revienta con
`ValueError: <Token ...> was created in a different Context`, y está escrito
en `rutas_tablero.py` para que nadie lo intente dos veces.

### 4.4 El menú no es la protección, y la interfaz lo dice


El menú se arma con `GET /api/permisos/mios`. **Y eso no protege nada:** es
HTML que ya está en el navegador de quien pregunta, y la dirección se puede
escribir a mano.

> **Se comprueba así, y es el criterio 9:** identifíquese con un rol sin
> permiso y **escriba la dirección a mano**. La interfaz se abre, le pide los
> datos a la API, y la API responde **403**. Eso es lo que tiene que pasar.

## 5. Los cinco tropiezos que esta versión tiene preparados

| | Qué pasa | Cómo se ve |
|---|---|---|
| **1** | **El `ClockSkew` por defecto** | FastAPI perdona **5 minutos** de reloj desadaptado. Un token vencido responde **200** durante cinco minutos, y parece que el código está mal. Se pone en cero |
| **2** | **El 401 sin cuerpo** | FastAPI responde el 401 con el cuerpo **vacío**, y la interfaz no tiene nada que mostrarle a la persona. Se arregla con `OnChallenge` |
| **3** | **`UseAuthentication` después de `UseAuthorization`** | Compila, arranca, y **deja pasar todo**: el segundo no tiene a quién consultar |
| **4** | **Una ruta que no está en la tabla** | `verificar_acceso_ruta` no la encuentra. Tiene que **fallar cerrado** —nadie entra— y no abierto |
| **5** | **`EstadoSesion` como `singleton`** | Un token para todos. No da ningún error: da la sesión de otro |

> **Los cinco pasan la compilación.** Tres de ellos —el 1, el 3 y el 5— dejan
> el sistema **menos seguro de lo que parece**, que es la peor clase de error:
> funciona, y por eso nadie lo mira.

## 6. Lo que este plan deja FUERA, a propósito

| | Por qué |
|---|---|
| **Refrescar el token** | Con una hora de duración, volver a identificarse alcanza. Un *refresh token* trae su propio problema —cómo se revoca— y el curso no lo pide |
| **Recuperar la contraseña por correo** | Hace falta un servidor de correo. No lo pide el curso |
| **Segundo factor** | Ídem |
| **Revocar un token** | **No se puede**, y es una propiedad del diseño, no un olvido: un JWT está firmado y ya salió. Lo único que lo apaga es que venza — de ahí que la duración sea corta |
| **Permisos por operación** (leer sí, borrar no) | La tabla `ruta` tiene `/permiso/crear` y `/permiso/eliminar` sembrados, así que la base de datos lo soportaría. **La v3 protege por interfaz**, que es lo que los diez criterios piden |
