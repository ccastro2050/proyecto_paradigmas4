"""
Controller de usuario-con-roles — el usuario y sus roles, en un solo envio.

Traduccion de excepciones (ver 6_contracts.md):
    body invalido        -> 422 (Pydantic: email, clave corta, lista vacia)
    ValueError           -> 400 (regla de negocio: sin rol no se crea)
    LookupError          -> 404 (lo levanta el procedimiento: «no existe»)
    ConflictoError       -> 409 (el usuario ya existe, o un rol no existe)
    cualquier otra       -> 500 (error del motor)

POR QUE ESTE RECURSO EXISTE SI YA HAY /api/usuario Y /api/rol-usuario
---------------------------------------------------------------------
Porque crear el usuario y asignarle sus roles con dos peticiones deja un
estado intermedio real: si la segunda falla, queda un usuario que no puede
hacer nada. Aqui las dos cosas ocurren DENTRO de un procedimiento, en una
transaccion del motor.

Y la comparacion que vale una clase entera: `/api/rol-usuario` es la MISMA
relacion vista como tabla puente cruda —una pareja a la vez—; esto es la
relacion vista como un documento —el usuario con su juego de roles—. Las dos
son legitimas, y sirven para cosas distintas. La pantalla de casillas usa
esta; una pantalla de administracion fina usa la otra.

Nota sobre el 422: la lista de roles vacia la rechaza Pydantic
(`min_length=1`) y la lista con ceros la rechaza el servicio (400). Dos
puertas para dos cosas distintas: la FORMA y la REGLA.
"""

from fastapi import APIRouter, Depends, HTTPException

from autorizacion.dependencias import exige_permiso
from excepciones import ConflictoError
from models.usuario_con_roles import (UsuarioConRolesActualizar,
                                      UsuarioConRolesCrear,
                                      UsuarioConRolesReemplazo)
from servicios.ensamblador import crear_servicio_usuario_con_roles

# ----------------------------------------------------------------------
# LA GUARDIA, en el router y no en cada endpoint (v3)
# ----------------------------------------------------------------------
# Exige la ruta «/usuario», la misma que /api/usuario y /api/rol-usuario:
# administrar usuarios es un solo permiso, aunque sean tres recursos. Si cada
# recurso pidiera el suyo, dar de alta a alguien exigiria tres permisos y
# nadie se acordaria de los tres.
router = APIRouter(prefix="/api/usuario-con-roles", tags=["UsuarioConRoles"],
                   dependencies=[Depends(exige_permiso("/usuario"))])


def _error(estado: int, mensaje: str, detalle: str) -> HTTPException:
    """Arma el sobre de error uniforme {estado, mensaje, detalle}."""
    return HTTPException(
        status_code=estado,
        detail={"estado": estado, "mensaje": mensaje, "detalle": detalle},
    )


# ----------------------------------------------------------------------
# GET /api/usuario-con-roles — todos, con sus roles
# ----------------------------------------------------------------------
@router.get("")
async def listar():
    try:
        datos = await crear_servicio_usuario_con_roles().listar()
    except Exception as exc:
        raise _error(500, "Error interno.", str(exc)) from exc
    # UNA consulta, no N+1: el procedimiento ya trae cada usuario con su
    # lista de roles. Pedir los usuarios y luego un viaje por cada uno daria
    # el mismo resultado y ocho veces el trabajo.
    return {"tabla": "usuario_con_roles", "total": len(datos), "datos": datos}


# ----------------------------------------------------------------------
# GET /api/usuario-con-roles/{email} — uno
# ----------------------------------------------------------------------
@router.get("/{email}")
async def consultar(email: str):
    try:
        return await crear_servicio_usuario_con_roles().consultar(email)
    except ValueError as exc:
        raise _error(400, "Solicitud invalida.", str(exc)) from exc
    except LookupError as exc:
        raise _error(404, "No encontrado.", str(exc)) from exc
    except Exception as exc:
        raise _error(500, "Error interno.", str(exc)) from exc


# ----------------------------------------------------------------------
# POST /api/usuario-con-roles — crear usuario Y roles, en una transaccion
# ----------------------------------------------------------------------
@router.post("", status_code=201)
async def crear(cuerpo: UsuarioConRolesCrear):
    try:
        return await crear_servicio_usuario_con_roles().crear(
            cuerpo.email, cuerpo.contrasena, cuerpo.roles)
    except ValueError as exc:
        raise _error(400, "Solicitud invalida.", str(exc)) from exc
    except ConflictoError as exc:
        raise _error(409, "La operacion choca con los datos que ya existen.",
                     str(exc)) from exc
    except Exception as exc:
        raise _error(500, "Error interno.", str(exc)) from exc


# ----------------------------------------------------------------------
# PUT /api/usuario-con-roles/{email} — el juego COMPLETO de roles
# ----------------------------------------------------------------------
@router.put("/{email}")
async def reemplazar(email: str, cuerpo: UsuarioConRolesReemplazo):
    try:
        return await crear_servicio_usuario_con_roles().actualizar(
            email, cuerpo.contrasena, cuerpo.roles)
    except ValueError as exc:
        raise _error(400, "Solicitud invalida.", str(exc)) from exc
    except LookupError as exc:
        raise _error(404, "No encontrado.", str(exc)) from exc
    except ConflictoError as exc:
        raise _error(409, "La operacion choca con los datos que ya existen.",
                     str(exc)) from exc
    except Exception as exc:
        raise _error(500, "Error interno.", str(exc)) from exc


# ----------------------------------------------------------------------
# PATCH /api/usuario-con-roles/{email} — solo lo que llegue
# ----------------------------------------------------------------------
@router.patch("/{email}")
async def actualizar(email: str, cuerpo: UsuarioConRolesActualizar):
    # exclude_unset distingue «mando roles: null» de «no mando roles», y esa
    # diferencia es justo la que el PATCH necesita.
    datos = cuerpo.model_dump(exclude_unset=True)
    if not datos:
        raise _error(400, "Solicitud invalida.",
                     "No se envio ningun campo para actualizar.")
    try:
        return await crear_servicio_usuario_con_roles().actualizar_parcial(
            email, datos.get("contrasena"), datos.get("roles"))
    except ValueError as exc:
        raise _error(400, "Solicitud invalida.", str(exc)) from exc
    except LookupError as exc:
        raise _error(404, "No encontrado.", str(exc)) from exc
    except ConflictoError as exc:
        raise _error(409, "La operacion choca con los datos que ya existen.",
                     str(exc)) from exc
    except Exception as exc:
        raise _error(500, "Error interno.", str(exc)) from exc


# ----------------------------------------------------------------------
# DELETE /api/usuario-con-roles/{email} — el usuario Y sus asignaciones
# ----------------------------------------------------------------------
@router.delete("/{email}")
async def eliminar(email: str):
    try:
        return await crear_servicio_usuario_con_roles().eliminar(email)
    except ValueError as exc:
        raise _error(400, "Solicitud invalida.", str(exc)) from exc
    except LookupError as exc:
        raise _error(404, "No encontrado.", str(exc)) from exc
    except Exception as exc:
        raise _error(500, "Error interno.", str(exc)) from exc
    # 200 con el mensaje del procedimiento, no 204: aqui se borraron filas de
    # DOS tablas, y decirlo es informacion util. En /api/usuario, que borra de
    # una sola, el 204 basta.
