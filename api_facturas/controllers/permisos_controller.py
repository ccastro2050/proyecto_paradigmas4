"""
Controller de permisos — lo que la interfaz necesita para armar su menu.

`GET /api/permisos/mios` devuelve las rutas a las que puede entrar QUIEN
LLAMA. El correo sale del token, asi que nadie puede preguntar por los
permisos de otro con este endpoint.

Y la advertencia que acompana a este recurso siempre:

**esta lista no protege nada.** Esconder una entrada del menu no es control
de acceso: quien escriba la direccion a mano llega igual. La proteccion esta
en `exige_permiso`, que corre en CADA peticion a CADA endpoint. Esto es para
que la pantalla no ofrezca lo que de todos modos va a dar 403.

Quien quiera ADMINISTRAR permisos —conceder, revocar, ver los de un rol— no
viene aqui: eso es el recurso `rutarol`, que para eso tiene sus cinco verbos
y su endpoint de lista completa. Dos recursos y no uno, porque son dos
preguntas distintas: «que puedo hacer yo» y «quien puede hacer que».
"""

from fastapi import APIRouter, Depends, HTTPException

from autorizacion.dependencias import usuario_actual
from servicios.ensamblador import crear_servicio_permisos

router = APIRouter(prefix="/api/permisos", tags=["Permisos"])


def _error(estado: int, mensaje: str, detalle: str) -> HTTPException:
    """Arma el sobre de error uniforme {estado, mensaje, detalle}."""
    return HTTPException(
        status_code=estado,
        detail={"estado": estado, "mensaje": mensaje, "detalle": detalle},
    )


# ----------------------------------------------------------------------
# GET /api/permisos/mios — las rutas de quien llama
# ----------------------------------------------------------------------
@router.get("/mios")
async def mios(quien: dict = Depends(usuario_actual)):
    try:
        rutas = await crear_servicio_permisos().mis_rutas(quien["email"])
    except ValueError as exc:
        raise _error(400, "Solicitud invalida.", str(exc)) from exc
    except Exception as exc:
        raise _error(500, "Error interno.", str(exc)) from exc
    return {"consulta": "mis rutas", "email": quien["email"],
            "roles": quien["roles"], "total": len(rutas), "datos": rutas}
