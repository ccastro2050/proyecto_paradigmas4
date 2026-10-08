# Plan de la versión 4 — Facturación (`bdfacturas`)

> **Qué es este documento.** Qué agrega la v4, qué se decidió antes de
> programarla, y **los cinco tropiezos que tiene preparados** — uno de los
> cuales no falla: **miente**, que es peor.
>
> El requisito que manda está en
> [`2_spec.md`](../spec_kit/versiones/v4_aplicativo/2_spec.md). Esto es el
> relato.
>
> **Material académico simulado** en el dominio; los tropiezos son reales, y
> dos de ellos **aparecieron comparando con el gemelo .NET del curso**.
>
> Versión 1.0 · 7 de octubre de 2026.

---

## 0. Lo que queda al terminar la v4

| Queda | Comprobable con |
|---|---|
| **Diez consultas** que cruzan cuatro o cinco tablas | `/api/consultas/ventas-por-producto` … y las otras nueve |
| El **tablero** que las muestra todas en una página | `localhost:8046/tablero` |
| `usuario-con-roles`: el usuario y sus roles **en un envío** | `POST /api/usuario-con-roles` con `{"email", "contrasena", "roles":[2,3]}` |
| Las **14 pantallas** del front, una por recurso | El menú, con sesión de `admin` |
| La API cerrada: **45 rutas, 85 operaciones**, 83 con permiso | `curl localhost:8005/openapi.json` |

---

## 1. De dónde se partió

La v3 dejó la API cerrada y con once recursos. Lo que **no** había:

| | |
|---|---|
| **Consultas** | Ninguna. Todo lo que la API sabía responder era de una tabla a la vez |
| **Tablero** | El blueprint del front **estaba escrito** —`rutas_tablero.py`, con su grupo de hilos y su plantilla—, comentado, esperando los endpoints |
| **`usuario-con-roles`** | Los cinco procedimientos estaban en la base de datos desde julio. Sin un solo llamador |

> **Otra vez el mismo patrón que en la v3**, y ya no es casualidad: lo que
> faltaba no era diseño. Era la llamada.

---

## 2. La decisión que define la versión: **el cruce se hace donde están los datos**

Las diez consultas podrían armarse en Python: pedir facturas, pedir renglones,
pedir productos, y cruzar con diccionarios. **No se hizo.**

| | Cruzando en Python | Cruzando en SQL |
|---|---|---|
| **Viajes a la base de datos** | Uno por tabla, y a veces uno por fila | **Uno** |
| **Datos que viajan** | Todas las filas, para quedarse con un resumen | Solo el resumen |
| **Quién hace el trabajo** | El proceso de la API | El motor, que para eso tiene índices |

Y el caso extremo: `ventas-por-producto` responde **8 filas** resumiendo
facturas, renglones, productos y clientes. Cruzando arriba habría que traer
todas las filas de cuatro tablas para devolver ocho.

> **La regla, en una línea: lo que se puede resumir abajo, se resume abajo.** Y
> su límite: lo que hay que **decidir** —si una operación se permite, si un
> dato es válido— sube al servicio. Resumir no es decidir.

### Una ruta por consulta, con nombre propio

Lo fácil sería `GET /api/consultas/{nombre}` y un diccionario de SQL adentro.
La API expone **diez rutas declaradas**, y las razones en orden de peso:

1. **El contrato se puede leer.** Swagger lista las diez por su nombre.
2. **El permiso se puede dar por consulta.** Hoy las diez exigen `/home`; el
   día que una sea solo para contabilidad, se cambia **una línea**.
3. **Lo que no está declarado no se puede pedir.** Un `{nombre}` que entra al
   SQL —aunque sea como llave de un diccionario— es una puerta que vigilar.

Y el front **sí** las pide por nombre variable (`consulta(nombre)` en
`cliente_api.py`), lo cual no contradice nada: **el cliente puede ser
genérico; el contrato, no.**

### Sin procedimientos, y es la decisión contraria a la de factura

La facturación va por procedimientos. Las diez consultas, no. **No es una
incoherencia: es el criterio.**

> Un procedimiento se justifica donde hay una **regla que proteger** —varias
> sentencias que tienen que valer como una—. Un reporte no protege nada: es un
> SELECT que cambia cada vez que alguien lo quiere ver de otra forma, y
> meterlo en la base obliga a tocarla para cambiar un `ORDER BY`.

---

## 3. La segunda decisión: **las diez se piden a la vez**

El tablero pide las diez consultas **en paralelo**, con un grupo de hilos. En
serie, con el tiempo máximo de 10 segundos por petición, abrir el tablero
podría costar un minuto y medio; en paralelo cuesta lo que la más lenta.

Y hay dos detalles que el código de `rutas_tablero.py` cuenta y conviene
leer:

| | |
|---|---|
| **Si una falla, las otras nueve se dibujan** | Un tablero que se cae entero porque una consulta tuvo un problema es peor que uno incompleto: no deja ver lo que sí está bien, y no dice cuál falló. El mensaje **nombra** la que falló |
| **El token se lee antes de abrir los hilos** | `session` pertenece al contexto de la petición de Flask, y un hilo nuevo no lo tiene. El camino que no sirvió —envolver con `copy_current_request_context`— revienta con `ValueError: <Token ...> was created in a different Context`, y está documentado en el archivo para que nadie lo intente dos veces |

---

## 4. El orden en que se construyó

| | Qué | Por qué en ese orden |
|---|---|---|
| **1** | `usuario-con-roles`, cinco procedimientos | Era lo que el front ya pedía y no existía |
| **2** | Las diez consultas en PostgreSQL | Escribirlas pensando, una sola vez |
| **3** | Las mismas en MariaDB y SQL Server | Derivadas, cambiando solo lo que el motor no acepta |
| **4** | Los diez endpoints y el servicio | Con el sobre `{consulta, total, datos}` |
| **5** | Encender el tablero y `usuarios-con-roles` en el front | Ya había a quién preguntarle |
| **6** | Las cuatro pantallas que faltaban | ruta, usuario y las dos puente |

---

## 5. Los cinco tropiezos que esta versión tiene preparados

| | Qué pasa | Por qué cuesta caro |
|---|---|---|
| **1. La división que trunca en T-SQL** | `COUNT()` devuelve `INT`, y en T-SQL dividir un `DECIMAL` entre un `INT` **trunca**: el ticket promedio sale sin centavos. PostgreSQL y MariaDB promueven el tipo solos | **No falla: miente.** La consulta corre, responde 200 y devuelve un número redondo que parece bueno. Un error que revienta se arregla; uno que miente se queda. Hace falta `CAST(... AS DECIMAL(18,2))` |
| **2. `STRING_AGG` no es igual en los tres** | PostgreSQL acepta `STRING_AGG(DISTINCT x, ', ')`. T-SQL **no admite DISTINCT** adentro —«Incorrect syntax near ','»— y MariaDB no tiene `STRING_AGG`: usa `GROUP_CONCAT` con `SEPARATOR` | Este sí falla a gritos, y es el más instructivo: **ocho de las diez consultas son idénticas palabra por palabra** en los tres motores. Lo que cambia son las funciones de agregación y las reglas de tipos |
| **3. El `LEFT JOIN` que nadie pone** | «Productos que nunca se han vendido» con `INNER JOIN` devuelve **vacío**, porque esos productos no tienen fila en el detalle | **Falla en silencio**: la consulta responde 200 con cero filas, y quien la lea concluye que **todo se vende**. Para preguntar por lo que NO está hace falta `LEFT JOIN` + `HAVING COUNT(...) = 0` |
| **4. El `CAST(... AS INT)` que aquí NO hace falta** | El gemelo .NET lleva `CAST(COUNT(...) AS INT)` en las diez consultas, porque `COUNT` devuelve `BIGINT` y el modelo de C# pedía `int`: sin el cast, 500 al materializar la primera fila | Aquí no hace falta, y la razón no es que Python sea mejor: **no hay modelo que materializar** —la fila llega como diccionario—. El precio se paga en el otro extremo: una columna de más en el SELECT, en C# la caza la librería; en Python llega en silencio hasta la pantalla. **Los dos lenguajes cobran, en momentos distintos** |
| **5. El PATCH sobre un procedimiento con semántica de PUT** | `actualizar_usuario_con_roles` **siempre** reemplaza los roles. Un PATCH que solo trae la contraseña, llamándolo tal cual, **deja al usuario sin roles** | **Falla en silencio y destruye datos**: la respuesta es 200. Se arregla leyendo los roles de ahora y volviéndolos a mandar — una consulta de más, pagada en el servicio y no retocando el procedimiento |

> **El cuarto no es un tropiezo de este repositorio: es el que explica para
> qué existe el curso.** El mismo sistema, escrito dos veces, cobra en sitios
> distintos. Quien solo haya visto uno de los dos cree que su lenguaje no
> cobra.

---

## 6. Cómo se verificó

Las diez, con la API arriba y sesión de `admin`:

```powershell
$s = Invoke-RestMethod -Method Post http://localhost:8005/api/sesion/entrar `
      -ContentType 'application/json' `
      -Body '{"email":"admin@correo.com","contrasena":"admin123"}'
$h = @{ Authorization = "Bearer $($s.token)" }

'ventas-por-producto','ventas-por-cliente','ventas-por-vendedor',
'ventas-por-empresa','ticket-por-vendedor','productos-sin-vender',
'anulaciones-por-cliente','alcance-de-usuarios','interfaces-sin-usuarios',
'credito-contra-consumo' | ForEach-Object {
    $r = Invoke-RestMethod "http://localhost:8005/api/consultas/$_" -Headers $h
    "{0,-26} {1}" -f $_, $r.total
}
```

Lo que respondió:

| Consulta | Filas |
|---|---|
| ventas-por-producto | 8 |
| ventas-por-cliente | 3 |
| ventas-por-vendedor | 3 |
| ventas-por-empresa | 2 |
| ticket-por-vendedor | 3 |
| **productos-sin-vender** | **0** |
| anulaciones-por-cliente | 2 |
| alcance-de-usuarios | 8 |
| **interfaces-sin-usuarios** | **0** |
| credito-contra-consumo | 6 |

> **Los dos ceros son el dato correcto, no una falla**: con los datos
> sembrados, todo producto se ha vendido alguna vez y toda ruta tiene quien
> entre. Confundir «vacío» con «roto» hace perder tardes enteras — y es la
> razón por la que estas dos consultas están en el tablero: el día que
> alguien siembre un producto nuevo, aparece ahí solo.

Y el tablero: **34 filas dibujadas, ninguna consulta caída**.

---

## 7. Lo que falta para cerrar la v4

| | |
|---|---|
| **Páginas corporativas** | Quiénes somos, contacto, políticas. El manual de marca está ([`MANUAL_DE_MARCA.md`](MANUAL_DE_MARCA.md)); las páginas no |
| **Publicación** | El aplicativo corre en `localhost`. Publicarlo es parte del enunciado de la v4 y no se ha hecho |
| **Retirar el token** | Ver [`PENDIENTES.md`](PENDIENTES.md) §2: hoy `DELETE /api/sesion` le dice al cliente que lo borre, y lo dice en su respuesta |

### Y después de la v4

**La v5: otros motores.** Y aquí hay algo que esta versión dejó medido y que
conviene decir en voz alta: las diez consultas **ya están escritas tres
veces**, una por dialecto, y los 42 repositorios también. La v5 no va a ser
«agregar MariaDB»: eso ya está hecho y probado. La v5 es **demostrarlo** —
cambiar `DB_PROVIDER` y que todo responda igual
([`DEMOSTRACION_MOTORES.md`](../DEMOSTRACION_MOTORES.md)).

> Eso es lo que paga la arquitectura de la v1: el día que llegó el tercer
> motor, costó **un bloque** en el ensamblador.
