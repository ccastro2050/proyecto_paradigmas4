"""
Controller de sesion — la puerta de la calle.

`POST /api/sesion/entrar` es el UNICO endpoint de la API al que se entra sin
token. Y tiene que ser asi, porque no puede exigir lo que todavia no existe.
Junto con el diagnostico `/`, son los dos unicos abiertos.

LA RESPUESTA AL FALLAR ES LA MISMA EN LOS DOS CASOS —correo inexistente y
contrasena equivocada—: 401, con el mismo texto. Un 404 para el primero le
confirmaria a un desconocido que correos SI existen (ver `servicio_sesion`).

Los otros tres endpoints SI exigen token, y hablan siempre de uno mismo: el
correo sale del token, nunca del body ni de la URL. Eso es lo que impide
usarlos para tocarle la sesion a otro.
"""

from fastapi import APIRouter, Depends, HTTPException

from autorizacion.dependencias import usuario_actual
from models.sesion import Credenciales
from servicios.ensamblador import crear_servicio_sesion

router = APIRouter(prefix="/api/sesion", tags=["Sesion"])


def _error(estado: int, mensaje: str, detalle: str) -> HTTPException:
    """Arma el sobre de error uniforme {estado, mensaje, detalle}."""
    return HTTPException(
        status_code=estado,
        detail={"estado": estado, "mensaje": mensaje, "detalle": detalle},
        headers={"WWW-Authenticate": "Bearer"} if estado == 401 else None,
    )


# ----------------------------------------------------------------------
# POST /api/sesion/entrar — SIN token (el unico)
# ----------------------------------------------------------------------
@router.post("/entrar")
async def entrar(credenciales: Credenciales):
    try:
        sesion = await crear_servicio_sesion().entrar(
            credenciales.email, credenciales.contrasena)
    except Exception as exc:
        raise _error(500, "Error interno.", str(exc)) from exc
    if sesion is None:
        # UN SOLO mensaje para los dos casos malos, a proposito.
        raise _error(401, "Credenciales invalidas.",
                     "El correo o la contrasena no coinciden.")
    return sesion


# ----------------------------------------------------------------------
# GET /api/sesion — quien soy, segun el token
# ----------------------------------------------------------------------
@router.get("")
async def quien_soy(quien: dict = Depends(usuario_actual)):
    """Lo que el token dice de quien llama.

    No consulta la base de datos: lee el token y ya. Sirve para que una
    interfaz sepa a nombre de quien esta trabajando sin guardar ese dato
    por su cuenta.
    """
    return {"email": quien["email"], "roles": quien["roles"]}


# ----------------------------------------------------------------------
# POST /api/sesion/renovar — un token nuevo, con los roles de HOY
# ----------------------------------------------------------------------
@router.post("/renovar")
async def renovar(quien: dict = Depends(usuario_actual)):
    try:
        sesion = await crear_servicio_sesion().renovar(quien["email"])
    except Exception as exc:
        raise _error(500, "Error interno.", str(exc)) from exc
    if sesion is None:
        raise _error(401, "No hay una sesion valida.",
                     "No se pudo renovar la sesion.")
    return sesion


# ----------------------------------------------------------------------
# DELETE /api/sesion — salir
# ----------------------------------------------------------------------
@router.delete("")
async def salir(quien: dict = Depends(usuario_actual)):
    """Cierra la sesion… del lado del cliente.

    Y hay que decirlo sin maquillaje: **este endpoint no invalida el token**.
    Un JWT es autocontenido: mientras no venza, sigue siendo valido, y el
    servidor no guarda ninguna lista de tokens vivos. Lo que hace este
    endpoint es confirmarle al cliente que borre el que tiene.

    Para invalidar de verdad haria falta una lista negra en la base de datos
    y una consulta por peticion —justo lo que un JWT viene a evitar—. Esa es
    la contrapartida de no guardar estado, y conviene conocerla antes de
    elegirlo. Mientras tanto, la defensa es que el token dure poco
    (`JWT_MINUTOS`).
    """
    return {"mensaje": "Sesion cerrada. Borre el token en el cliente.",
            "email": quien["email"],
            "advertencia": "El token sigue siendo valido hasta que venza."}
