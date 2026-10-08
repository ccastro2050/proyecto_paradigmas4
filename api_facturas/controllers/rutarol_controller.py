"""
Controller de rutarol — la capa HTTP del puente ruta <-> rol.

Traduccion de excepciones (ver 6_contracts.md):
    body invalido        -> 422 (Pydantic: un id que no es entero positivo)
    ValueError           -> 400 (los ids que vienen EN LA URL)
    LookupError          -> 404 (la pareja no existe)
    ConflictoError       -> 409 (ya existe, o uno de los dos ids no existe)
    cualquier otra       -> 500 (error del motor)

CINCO ENDPOINTS, Y NO SON LOS CINCO VERBOS
------------------------------------------
    GET    /api/rutarol                      las parejas, con los nombres
    GET    /api/rutarol/ruta/{id_ruta}       que roles entran a esta ruta
    GET    /api/rutarol/rol/{id_rol}         a que rutas entra este rol
    POST   /api/rutarol                      asignar
    DELETE /api/rutarol/{id_ruta}/{id_rol}   quitar esa asignacion exacta

**No hay PUT ni PATCH, y no es un olvido.** En una tabla puente las dos
columnas SON la llave: no hay un campo suelto que modificar, y una pareja
existe o no existe. Lo que seria «actualizar» —mover la pareja— se hace con
el DELETE y el POST que si estan.

Los dos verbos estan escritos mas abajo y **apagados**, con la explicacion
completa. Esa decision es deliberada: el contrato manda, y una API no lleva
todos los verbos en todos los recursos.

| Verbo | En una entidad | En este puente |
|---|---|---|
| POST | crea una fila | asigna un rol a una ruta |
| DELETE | borra la fila | quita esa asignacion exacta |
| PUT | reemplaza los campos | *(apagado)* MOVERIA la pareja: borrar una e insertar otra |
| PATCH | cambia un campo | *(apagado)* moveria UN LADO y conservaria el otro |
"""

from fastapi import APIRouter, Depends, HTTPException

from autorizacion.dependencias import exige_permiso
from excepciones import ConflictoError
# `RutaRolActualizar` y `RutasDeRol` los usa SOLO el codigo apagado del
# final del archivo. Se importan igual: si se quitaran, encender ese
# endpoint pediria dos cambios en vez de uno —y el segundo es el que se
# olvida—.
from models.rutarol import RutaRolActualizar, RutaRolCrear, RutasDeRol
from servicios.ensamblador import crear_servicio_rutarol

# ----------------------------------------------------------------------
# LA GUARDIA, en el router y no en cada endpoint (v3)
# ----------------------------------------------------------------------
# `exige_permiso` corre ANTES del cuerpo de CUALQUIER endpoint de este
# archivo, y por dentro hace dos preguntas: hay token valido? (si no, 401) y
# tiene este correo la ruta «/permiso»? (si no, 403). La consulta la responde
# `verificar_acceso_ruta`, en la base de datos, EN CADA PETICION.
#
# Va en el router a proposito: asi un endpoint nuevo en este archivo nace
# protegido. Endpoint por endpoint, el dia que alguien agregue uno y se le
# olvide, queda abierto —y nadie lo nota, porque funciona—.
router = APIRouter(prefix="/api", tags=["RutaRol (puente)"],
                   dependencies=[Depends(exige_permiso("/permiso"))])


def _error(estado: int, mensaje: str, detalle: str) -> HTTPException:
    """Arma el sobre de error uniforme {estado, mensaje, detalle}."""
    return HTTPException(
        status_code=estado,
        detail={"estado": estado, "mensaje": mensaje, "detalle": detalle},
    )


# ----------------------------------------------------------------------
# GET /api/rutarol — Listar las parejas, con los nombres
# ----------------------------------------------------------------------
@router.get("/rutarol")
async def listar(limite: int = 1000):
    try:
        datos = await crear_servicio_rutarol().listar(limite)
    except Exception as exc:
        raise _error(500, "Error interno.", str(exc)) from exc
    return {"tabla": "rutarol", "limite": limite, "total": len(datos),
            "datos": datos}


# ----------------------------------------------------------------------
# GET /api/rutarol/ruta/{id_ruta} — Que roles entran a esta ruta
# ----------------------------------------------------------------------
@router.get("/rutarol/ruta/{id_ruta}")
async def listar_por_ruta(id_ruta: int):
    try:
        datos = await crear_servicio_rutarol().listar_por_ruta(id_ruta)
    except ValueError as exc:
        raise _error(400, "Solicitud invalida.", str(exc)) from exc
    except Exception as exc:
        raise _error(500, "Error interno.", str(exc)) from exc
    # Una lista vacia NO es un 404: la ruta puede existir y no tener roles
    # asignados todavia. 404 seria «esa ruta no existe», que es otra cosa.
    return {"consulta": "roles de la ruta", "fkidruta": id_ruta,
            "total": len(datos), "datos": datos}


# ----------------------------------------------------------------------
# GET /api/rutarol/rol/{id_rol} — A que rutas entra este rol
# ----------------------------------------------------------------------
@router.get("/rutarol/rol/{id_rol}")
async def listar_por_rol(id_rol: int):
    try:
        datos = await crear_servicio_rutarol().listar_por_rol(id_rol)
    except ValueError as exc:
        raise _error(400, "Solicitud invalida.", str(exc)) from exc
    except Exception as exc:
        raise _error(500, "Error interno.", str(exc)) from exc
    return {"consulta": "rutas del rol", "fkidrol": id_rol,
            "total": len(datos), "datos": datos}


# ----------------------------------------------------------------------
# POST /api/rutarol — Asignar un rol a una ruta
# ----------------------------------------------------------------------
@router.post("/rutarol", status_code=201)
async def crear(asignacion: RutaRolCrear):
    try:
        await crear_servicio_rutarol().crear(asignacion.fkidruta,
                                             asignacion.fkidrol)
    except ValueError as exc:
        raise _error(400, "Solicitud invalida.", str(exc)) from exc
    except ConflictoError as exc:
        raise _error(409, "La asignacion choca con los datos que ya existen.",
                     str(exc)) from exc
    except Exception as exc:
        raise _error(500, "Error interno.", str(exc)) from exc
    return {"mensaje": "Permiso asignado.", "fkidruta": asignacion.fkidruta,
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
#      pasa y el INSERT falla, el rol no queda como estaba —queda peor—.
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
# # PUT /api/rutarol/rol/{id_rol} — TODAS las rutas de un rol, de una vez
# # (va ANTES del PUT de la pareja: una ruta fija se declara antes que una
# #  ruta con dos parametros que podria confundirse con ella)
# # ----------------------------------------------------------------------
# @router.put("/rutarol/rol/{id_rol}")
# async def reemplazar_rutas_del_rol(id_rol: int, cuerpo: RutasDeRol):
#     try:
#         cuantas = await crear_servicio_rutarol().reemplazar_de_rol(
#             id_rol, cuerpo.ids_ruta)
#     except ValueError as exc:
#         raise _error(400, "Solicitud invalida.", str(exc)) from exc
#     except ConflictoError as exc:
#         raise _error(409, "La lista choca con los datos que ya existen.",
#                      str(exc)) from exc
#     except Exception as exc:
#         raise _error(500, "Error interno.", str(exc)) from exc
#     # Una lista vacia es legal: deja al rol sin permisos (ver el servicio).
#     return {"mensaje": "Rutas del rol reemplazadas.", "fkidrol": id_rol,
#             "rutas": cuantas}
#
#
# # ----------------------------------------------------------------------
# # PUT /api/rutarol/{id_ruta}/{id_rol} — MOVER el permiso
# # ----------------------------------------------------------------------
# @router.put("/rutarol/{id_ruta}/{id_rol}")
# async def reemplazar(id_ruta: int, id_rol: int, nueva: RutaRolCrear):
#     # La pareja de la URL es la que existe hoy; la del body, la que queda.
#     try:
#         await crear_servicio_rutarol().reemplazar(
#             id_ruta, id_rol, nueva.fkidruta, nueva.fkidrol)
#     except ValueError as exc:
#         raise _error(400, "Solicitud invalida.", str(exc)) from exc
#     except LookupError as exc:
#         raise _error(404, "No encontrado.", str(exc)) from exc
#     except ConflictoError as exc:
#         raise _error(409, "La pareja nueva choca con los datos que ya "
#                           "existen.", str(exc)) from exc
#     except Exception as exc:
#         raise _error(500, "Error interno.", str(exc)) from exc
#     return {"mensaje": "Permiso movido.",
#             "antes": {"fkidruta": id_ruta, "fkidrol": id_rol},
#             "ahora": {"fkidruta": nueva.fkidruta, "fkidrol": nueva.fkidrol}}
#
#
# # ----------------------------------------------------------------------
# # PATCH /api/rutarol/{id_ruta}/{id_rol} — mover UN lado
# # ----------------------------------------------------------------------
# @router.patch("/rutarol/{id_ruta}/{id_rol}")
# async def actualizar(id_ruta: int, id_rol: int, cambio: RutaRolActualizar):
#     # Lo que no llega se conserva: `{"fkidrol": 3}` le pasa esta ruta a otro
#     # rol y deja la ruta como estaba. Esa es toda la diferencia con el PUT.
#     datos = cambio.model_dump(exclude_unset=True)
#     if not datos:
#         raise _error(400, "Solicitud invalida.",
#                      "No se envio ningun lado para mover.")
#     try:
#         await crear_servicio_rutarol().reemplazar(
#             id_ruta, id_rol,
#             datos.get("fkidruta") or id_ruta,
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
#     return {"mensaje": "Permiso actualizado.",
#             "antes": {"fkidruta": id_ruta, "fkidrol": id_rol},
#             "ahora": {"fkidruta": datos.get("fkidruta") or id_ruta,
#                       "fkidrol": datos.get("fkidrol") or id_rol}}


# ----------------------------------------------------------------------
# DELETE /api/rutarol/{id_ruta}/{id_rol} — quitar ESA asignacion
# ----------------------------------------------------------------------
@router.delete("/rutarol/{id_ruta}/{id_rol}")
async def eliminar(id_ruta: int, id_rol: int):
    try:
        filas = await crear_servicio_rutarol().eliminar(id_ruta, id_rol)
    except ValueError as exc:
        raise _error(400, "Solicitud invalida.", str(exc)) from exc
    except Exception as exc:
        raise _error(500, "Error interno.", str(exc)) from exc
    if filas == 0:
        raise _error(404, "No encontrado.",
                     f"No existe el permiso ({id_ruta}, {id_rol}).")
    # 200 con cuerpo, no 204: aqui el cliente agradece saber CUANTAS filas
    # se fueron, porque en un puente es facil creer que se borro una y
    # haber borrado otra.
    return {"mensaje": "Permiso eliminado.", "filas_eliminadas": filas}
