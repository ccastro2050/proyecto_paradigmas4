"""
Controller de consultas — las DIEZ rutas del tablero de la v4.

DIEZ RUTAS, NO UNA CON PARAMETRO
--------------------------------
Lo facil seria `GET /api/consultas/{nombre}` y un diccionario de SQL adentro.
Esta API no lo hace, y es la misma regla que gobierna todo el proyecto: **una
ruta por recurso, declarada**. Las razones, en orden de peso:

1. **El contrato se puede leer.** Swagger lista las diez con su nombre. Con
   una ruta generica, Swagger dice «consultas/{nombre}» y el cliente tiene
   que adivinar o preguntar.
2. **El permiso se puede dar por consulta.** Hoy las diez exigen la ruta
   `/home`; el dia que una sea solo para contabilidad, se cambia esa linea.
   Con una ruta generica habria que inventar un mapa aparte.
3. **Lo que no esta declarado no se puede pedir.** Un `{nombre}` que entra al
   SQL —aunque sea como llave de un diccionario— es una puerta que hay que
   vigilar. Diez funciones no tienen nada que vigilar.

Y el front SI usa un nombre variable para pedirlas —`consulta(nombre)` en
`cliente_api.py`—, lo cual no contradice nada: **el cliente puede ser
generico; el contrato, no.** El que recibe «cual pedir» es el codigo del
front, no la API.

EL SOBRE ES OTRO QUE EL DEL CRUD
--------------------------------
    CRUD       {tabla, limite, total, datos}
    consulta   {consulta, total, datos}

Una consulta no tiene tabla —cruza cuatro o cinco— ni limite —devuelve lo que
hay—. Tiene nombre. Cambiar el sobre a medias seria peor: quien lea `tabla`
en una consulta no encontraria nada y leeria una lista vacia SIN error.
"""

from fastapi import APIRouter, Depends, HTTPException

from autorizacion.dependencias import exige_permiso
from servicios.ensamblador import crear_servicio_consultas

# ----------------------------------------------------------------------
# LA GUARDIA: las diez exigen `/home`
# ----------------------------------------------------------------------
# El tablero es la pagina de inicio, y su permiso es el de entrar al
# aplicativo. Hoy lo tienen los cinco roles: cualquiera que entre ve el
# tablero. Si manana una consulta fuera reservada, se le pone su propia
# dependencia a ESE endpoint —por eso estan los diez separados—.
router = APIRouter(prefix="/api/consultas", tags=["Consultas (v4)"],
                   dependencies=[Depends(exige_permiso("/home"))])


def _error(estado: int, mensaje: str, detalle: str) -> HTTPException:
    """Arma el sobre de error uniforme {estado, mensaje, detalle}."""
    return HTTPException(
        status_code=estado,
        detail={"estado": estado, "mensaje": mensaje, "detalle": detalle},
    )


async def _responder(nombre: str, corutina):
    """El sobre de las consultas, en un solo sitio.

    Diez endpoints que armaran el diccionario a mano serian diez sitios donde
    equivocarse con el nombre de una clave.
    """
    try:
        datos = await corutina
    except Exception as exc:
        raise _error(500, "Error interno.", str(exc)) from exc
    return {"consulta": nombre, "total": len(datos), "datos": datos}


# ----------------------------------------------------------------------
# Las diez
# ----------------------------------------------------------------------
@router.get("/ventas-por-producto")
async def ventas_por_producto():
    """Que se vende y cuanto deja. Cruza producto, renglon, factura, cliente."""
    return await _responder("ventas-por-producto",
                            crear_servicio_consultas().ventas_por_producto())


@router.get("/ventas-por-cliente")
async def ventas_por_cliente():
    """Quien compra y cuanto. Cruza cliente, persona, factura, renglon."""
    return await _responder("ventas-por-cliente",
                            crear_servicio_consultas().ventas_por_cliente())


@router.get("/ventas-por-vendedor")
async def ventas_por_vendedor():
    """Quien vende y cuanto. Cruza vendedor, persona, factura, renglon."""
    return await _responder("ventas-por-vendedor",
                            crear_servicio_consultas().ventas_por_vendedor())


@router.get("/ventas-por-empresa")
async def ventas_por_empresa():
    """Cuanto factura cada empresa. Cruza empresa, cliente, factura, renglon."""
    return await _responder("ventas-por-empresa",
                            crear_servicio_consultas().ventas_por_empresa())


@router.get("/ticket-por-vendedor")
async def ticket_por_vendedor():
    """Cuanto vale en promedio una factura de cada vendedor.

    Es la consulta que en SQL Server hay que escribir distinto: alli la
    division de un decimal entre un entero trunca (ver el repositorio).
    """
    return await _responder("ticket-por-vendedor",
                            crear_servicio_consultas().ticket_por_vendedor())


@router.get("/productos-sin-vender")
async def productos_sin_vender():
    """Lo que nadie ha comprado nunca. La unica con LEFT JOIN y HAVING = 0."""
    return await _responder("productos-sin-vender",
                            crear_servicio_consultas().productos_sin_vender())


@router.get("/anulaciones-por-cliente")
async def anulaciones_por_cliente():
    """Quien anula y por cuanto. Se puede preguntar porque la factura anulada
    NO se borra: cambia de estado."""
    return await _responder(
        "anulaciones-por-cliente",
        crear_servicio_consultas().anulaciones_por_cliente())


@router.get("/alcance-de-usuarios")
async def alcance_de_usuarios():
    """A cuantas interfaces llega cada usuario. CINCO tablas: es el camino
    completo del control de acceso, visto como reporte."""
    return await _responder("alcance-de-usuarios",
                            crear_servicio_consultas().alcance_de_usuarios())


@router.get("/interfaces-sin-usuarios")
async def interfaces_sin_usuarios():
    """Rutas a las que NADIE puede entrar: permisos declarados y muertos."""
    return await _responder(
        "interfaces-sin-usuarios",
        crear_servicio_consultas().interfaces_sin_usuarios())


@router.get("/credito-contra-consumo")
async def credito_contra_consumo():
    """Cuanto credito tiene cada cliente y cuanto se ha gastado."""
    return await _responder(
        "credito-contra-consumo",
        crear_servicio_consultas().credito_contra_consumo())
