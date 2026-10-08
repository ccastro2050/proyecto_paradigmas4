"""
Controller de rol_usuario — la capa HTTP del puente usuario <-> rol.

Traduccion de excepciones (ver 6_contracts.md):
    body invalido        -> 422 (Pydantic: email mal formado, id no positivo)
    ValueError           -> 400 (lo que viene EN LA URL)
    LookupError          -> 404 (la pareja o el usuario no existen)
    ConflictoError       -> 409 (ya existe, o el usuario o el rol no existen)
    cualquier otra       -> 500 (error del motor)

El prefijo del recurso es `/api/rol-usuario` —con guion—, aunque la tabla se
llame `rol_usuario`. No es un descuido: en una URL se estila el guion, y en
SQL el guion bajo. Cada capa escribe en su idioma, y el repositorio es el
unico que tiene que saber los dos.

CINCO ENDPOINTS, los mismos cinco de `rutarol`
----------------------------------------------
    GET    /api/rol-usuario                      las parejas, con el nombre del rol
    GET    /api/rol-usuario/usuario/{email}      que roles tiene este usuario
    GET    /api/rol-usuario/rol/{id_rol}         que usuarios tienen este rol
    POST   /api/rol-usuario                      dar un rol
    DELETE /api/rol-usuario/{email}/{id_rol}     quitar ESE rol

**Sin PUT ni PATCH**, por lo mismo que en `rutarol`: las dos columnas son la
llave y una pareja existe o no existe (la explicacion completa esta en ese
controller y, apagada, mas abajo).

Y lo propio de ESTE puente, que tambien esta apagado y vale leerlo:
`PUT /api/rol-usuario/usuario/{email}` mandaria la lista completa de roles, y
por debajo **no abre una transaccion en Python**: llama al procedimiento
`actualizar_roles_usuario`, que ya hace eso en la base de datos.

> **Quien necesite esa operacion la tiene**, y ahi esta la clave de por que
> apagarla aqui no le quita nada al sistema: `PUT /api/usuario-con-roles/{email}`
> hace exactamente eso, es parte del contrato, y es la que usa la pantalla de
> casillas. **La misma relacion, dos recursos, un solo sitio donde se
> escribe.**
"""

from fastapi import APIRouter, Depends, HTTPException

from autorizacion.dependencias import exige_permiso
from excepciones import ConflictoError
# `RolesDeUsuario` y `RolUsuarioActualizar` los usa SOLO el codigo apagado
# del final del archivo. Se importan igual: encender el endpoint tiene que
# ser quitar almohadillas y nada mas.
from models.rol_usuario import (RolesDeUsuario, RolUsuarioActualizar,
                                RolUsuarioCrear)
from servicios.ensamblador import crear_servicio_rol_usuario

# ----------------------------------------------------------------------
# LA GUARDIA, en el router y no en cada endpoint (v3)
# ----------------------------------------------------------------------
# `exige_permiso` corre ANTES del cuerpo de CUALQUIER endpoint de este
# archivo, y por dentro hace dos preguntas: hay token valido? (si no, 401) y
# tiene este correo la ruta «/usuario»? (si no, 403). La consulta la responde
# `verificar_acceso_ruta`, en la base de datos, EN CADA PETICION.
#
# Va en el router a proposito: asi un endpoint nuevo en este archivo nace
# protegido. Endpoint por endpoint, el dia que alguien agregue uno y se le
# olvide, queda abierto —y nadie lo nota, porque funciona—.
router = APIRouter(prefix="/api", tags=["RolUsuario (puente)"],
                   dependencies=[Depends(exige_permiso("/usuario"))])


def _error(estado: int, mensaje: str, detalle: str) -> HTTPException:
    """Arma el sobre de error uniforme {estado, mensaje, detalle}."""
    return HTTPException(
        status_code=estado,
        detail={"estado": estado, "mensaje": mensaje, "detalle": detalle},
    )


# ----------------------------------------------------------------------
# GET /api/rol-usuario — Listar las parejas, con el nombre del rol
# ----------------------------------------------------------------------
@router.get("/rol-usuario")
async def listar(limite: int = 1000):
    try:
        datos = await crear_servicio_rol_usuario().listar(limite)
    except Exception as exc:
        raise _error(500, "Error interno.", str(exc)) from exc
    return {"tabla": "rol_usuario", "limite": limite, "total": len(datos),
            "datos": datos}


# ----------------------------------------------------------------------
# GET /api/rol-usuario/usuario/{email} — Que roles tiene este usuario
# ----------------------------------------------------------------------
@router.get("/rol-usuario/usuario/{email}")
async def listar_por_usuario(email: str):
    try:
        datos = await crear_servicio_rol_usuario().listar_por_usuario(email)
    except ValueError as exc:
        raise _error(400, "Solicitud invalida.", str(exc)) from exc
    except Exception as exc:
        raise _error(500, "Error interno.", str(exc)) from exc
    # Lista vacia NO es 404: el usuario puede existir sin roles todavia.
    return {"consulta": "roles del usuario", "fkemail": email,
            "total": len(datos), "datos": datos}


# ----------------------------------------------------------------------
# GET /api/rol-usuario/rol/{id_rol} — Que usuarios tienen este rol
# ----------------------------------------------------------------------
@router.get("/rol-usuario/rol/{id_rol}")
async def listar_por_rol(id_rol: int):
    try:
        datos = await crear_servicio_rol_usuario().listar_por_rol(id_rol)
    except ValueError as exc:
        raise _error(400, "Solicitud invalida.", str(exc)) from exc
    except Exception as exc:
        raise _error(500, "Error interno.", str(exc)) from exc
    return {"consulta": "usuarios del rol", "fkidrol": id_rol,
            "total": len(datos), "datos": datos}


# ----------------------------------------------------------------------
# POST /api/rol-usuario — Dar un rol a un usuario
# ----------------------------------------------------------------------
@router.post("/rol-usuario", status_code=201)
async def crear(asignacion: RolUsuarioCrear):
    try:
        await crear_servicio_rol_usuario().crear(asignacion.fkemail,
                                                 asignacion.fkidrol)
    except ValueError as exc:
        raise _error(400, "Solicitud invalida.", str(exc)) from exc
    except ConflictoError as exc:
        raise _error(409, "La asignacion choca con los datos que ya existen.",
                     str(exc)) from exc
    except Exception as exc:
        raise _error(500, "Error interno.", str(exc)) from exc
    return {"mensaje": "Rol asignado.", "fkemail": asignacion.fkemail,
            "fkidrol": asignacion.fkidrol}


# ====================================================================
# APAGADOS POR ASUNTOS DIDACTICOS: el PUT, el PATCH y la lista completa
# ====================================================================
#
# ESTOS TRES ENDPOINTS NO VAN EN LA API, Y ESTAN AQUI A PROPOSITO: son
# material de clase, no codigo muerto que a alguien se le olvido borrar.
#
# POR QUE NO VAN
# --------------
# El contrato de la v3 declara CINCO endpoints para esta puente —listar, por
# cada lado, crear y quitar la pareja— y ni el PUT ni el PATCH son uno de
# ellos. La razon no es de gusto: en una tabla puente **una pareja existe o
# no existe**. Las dos columnas SON la llave, asi que no hay un campo suelto
# que modificar, y «actualizar» solo puede significar MOVER la fila: borrar
# una e insertar otra. Eso ya se puede hacer con el DELETE y el POST que si
# estan.
#
# POR QUE ENTONCES ESTAN ESCRITOS
# -------------------------------
# Porque hay dos cosas que aprender y las dos importan:
#
#   1. COMO SE PROGRAMA el verbo. Esta abajo, completo y comentado: el
#      reemplazo de una pareja va en UNA transaccion, porque si el DELETE
#      pasa y el INSERT falla, el usuario no queda como estaba —queda peor—.
#   2. Que una API NO lleva todos los verbos en todos los recursos. **El
#      contrato manda**, y el contrato dice que estos no.
#
# Borrarlos ensenaria solo la segunda; dejarlos apagados ensena las dos.
#
# PARA ENCENDERLOS basta con quitar las almohadillas de estas lineas: lo que
# hay debajo en el servicio y en el repositorio **SI esta activo** —y eso
# tambien es parte de la leccion: la capa de negocio puede saber hacer cosas
# que la API decide no ofrecer—.
#
# Y UNA ADVERTENCIA SI SE ENCIENDEN: el contrato cambia. Habria que
# actualizar 6_contracts.md, la coleccion de Postman y el gemelo .NET del
# curso, que hoy expone los mismos cinco.
#
# # ----------------------------------------------------------------------
# # PUT /api/rol-usuario/usuario/{email} — TODOS los roles, de una vez
# # (va ANTES del PUT de la pareja: la ruta fija primero)
# # ----------------------------------------------------------------------
# @router.put("/rol-usuario/usuario/{email}")
# async def reemplazar_roles_del_usuario(email: str, cuerpo: RolesDeUsuario):
#     try:
#         resultado = await crear_servicio_rol_usuario().reemplazar_roles(
#             email, cuerpo.ids_rol)
#     except ValueError as exc:
#         raise _error(400, "Solicitud invalida.", str(exc)) from exc
#     except LookupError as exc:
#         # Quien decide esto es el procedimiento de la base de datos:
#         # «Usuario % no existe» llega aqui convertido en LookupError.
#         raise _error(404, "No encontrado.", str(exc)) from exc
#     except ConflictoError as exc:
#         raise _error(409, "La lista choca con los datos que ya existen.",
#                      str(exc)) from exc
#     except Exception as exc:
#         raise _error(500, "Error interno.", str(exc)) from exc
#     # El procedimiento devuelve {email, roles}: se pasa tal cual, porque es
#     # el estado que quedo —no lo que se pidio—.
#     return {"mensaje": "Roles del usuario reemplazados.", "datos": resultado}
#
#
# # ----------------------------------------------------------------------
# # PUT /api/rol-usuario/{email}/{id_rol} — MOVER la pareja
# # ----------------------------------------------------------------------
# @router.put("/rol-usuario/{email}/{id_rol}")
# async def reemplazar(email: str, id_rol: int, nueva: RolUsuarioCrear):
#     try:
#         await crear_servicio_rol_usuario().reemplazar(
#             email, id_rol, nueva.fkemail, nueva.fkidrol)
#     except ValueError as exc:
#         raise _error(400, "Solicitud invalida.", str(exc)) from exc
#     except LookupError as exc:
#         raise _error(404, "No encontrado.", str(exc)) from exc
#     except ConflictoError as exc:
#         raise _error(409, "La pareja nueva choca con los datos que ya "
#                           "existen.", str(exc)) from exc
#     except Exception as exc:
#         raise _error(500, "Error interno.", str(exc)) from exc
#     return {"mensaje": "Asignacion movida.",
#             "antes": {"fkemail": email, "fkidrol": id_rol},
#             "ahora": {"fkemail": nueva.fkemail, "fkidrol": nueva.fkidrol}}
#
#
# # ----------------------------------------------------------------------
# # PATCH /api/rol-usuario/{email}/{id_rol} — mover UN lado
# # ----------------------------------------------------------------------
# @router.patch("/rol-usuario/{email}/{id_rol}")
# async def actualizar(email: str, id_rol: int, cambio: RolUsuarioActualizar):
#     datos = cambio.model_dump(exclude_unset=True)
#     if not datos:
#         raise _error(400, "Solicitud invalida.",
#                      "No se envio ningun lado para mover.")
#     try:
#         await crear_servicio_rol_usuario().reemplazar(
#             email, id_rol,
#             datos.get("fkemail") or email,
#             datos.get("fkidrol") or id_rol)
#     except ValueError as exc:
#         raise _error(400, "Solicitud invalida.", str(exc)) from exc
#     except LookupError as exc:
#         raise _error(404, "No encontrado.", str(exc)) from exc
#     except ConflictoError as exc:
#         raise _error(409, "La pareja nueva choca con los datos que ya "
#                           "existen.", str(exc)) from exc
#     except Exception as exc:
#         raise _error(500, "Error interno.", str(exc)) from exc
#     return {"mensaje": "Asignacion actualizada.",
#             "antes": {"fkemail": email, "fkidrol": id_rol},
#             "ahora": {"fkemail": datos.get("fkemail") or email,
#                       "fkidrol": datos.get("fkidrol") or id_rol}}


# ----------------------------------------------------------------------
# DELETE /api/rol-usuario/{email}/{id_rol} — quitar ESE rol
# ----------------------------------------------------------------------
@router.delete("/rol-usuario/{email}/{id_rol}")
async def eliminar(email: str, id_rol: int):
    try:
        filas = await crear_servicio_rol_usuario().eliminar(email, id_rol)
    except ValueError as exc:
        raise _error(400, "Solicitud invalida.", str(exc)) from exc
    except Exception as exc:
        raise _error(500, "Error interno.", str(exc)) from exc
    if filas == 0:
        raise _error(404, "No encontrado.",
                     f"El usuario {email} no tiene el rol {id_rol}.")
    return {"mensaje": "Rol quitado.", "filas_eliminadas": filas}
