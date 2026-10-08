"""
Controller de rutarol — la capa HTTP del puente ruta <-> rol.

Traduccion de excepciones (ver 6_contracts.md):
    body invalido        -> 422 (Pydantic: un id que no es entero positivo)
    ValueError           -> 400 (los ids que vienen EN LA URL)
    LookupError          -> 404 (la pareja no existe)
    ConflictoError       -> 409 (ya existe, o uno de los dos ids no existe)
    cualquier otra       -> 500 (error del motor)

QUE SIGNIFICA CADA VERBO EN UNA TABLA PUENTE
--------------------------------------------
Aqui no hay campos sueltos que cambiar: las dos columnas SON la llave. Eso
no quiere decir que falten verbos; quiere decir que cada uno significa otra
cosa, y vale la pena decirlo en voz alta:

| Verbo | En una entidad | En este puente |
|---|---|---|
| POST | crea una fila | asigna un rol a una ruta |
| PUT | reemplaza los campos | MUEVE la pareja: borra una e inserta otra |
| PATCH | cambia un campo | mueve UN LADO y conserva el otro |
| DELETE | borra la fila | quita esa asignacion exacta |

El PUT y el PATCH van en una TRANSACCION porque son dos sentencias que
tienen que valer como una: si el DELETE pasa y el INSERT falla, el rol no
queda como estaba —queda sin permiso—.

Y hay un sexto endpoint que no es ninguno de los cinco:
`PUT /api/rutarol/rol/{id_rol}` recibe LA LISTA COMPLETA de rutas de un rol.
Es el que de verdad usa una pantalla de permisos, donde el administrador
marca casillas y guarda una vez. Hacer eso con un DELETE y varios POST
dejaria al rol a medio camino si uno de los POST falla.
"""

from fastapi import APIRouter, HTTPException

from excepciones import ConflictoError
from models.rutarol import RutaRolActualizar, RutaRolCrear, RutasDeRol
from servicios.ensamblador import crear_servicio_rutarol

router = APIRouter(prefix="/api", tags=["RutaRol (puente)"])


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


# ----------------------------------------------------------------------
# PUT /api/rutarol/rol/{id_rol} — TODAS las rutas de un rol, de una vez
# (va ANTES del PUT de la pareja: una ruta fija se declara antes que una
#  ruta con dos parametros que podria confundirse con ella)
# ----------------------------------------------------------------------
@router.put("/rutarol/rol/{id_rol}")
async def reemplazar_rutas_del_rol(id_rol: int, cuerpo: RutasDeRol):
    try:
        cuantas = await crear_servicio_rutarol().reemplazar_de_rol(
            id_rol, cuerpo.ids_ruta)
    except ValueError as exc:
        raise _error(400, "Solicitud invalida.", str(exc)) from exc
    except ConflictoError as exc:
        raise _error(409, "La lista choca con los datos que ya existen.",
                     str(exc)) from exc
    except Exception as exc:
        raise _error(500, "Error interno.", str(exc)) from exc
    # Una lista vacia es legal: deja al rol sin permisos (ver el servicio).
    return {"mensaje": "Rutas del rol reemplazadas.", "fkidrol": id_rol,
            "rutas": cuantas}


# ----------------------------------------------------------------------
# PUT /api/rutarol/{id_ruta}/{id_rol} — MOVER el permiso
# ----------------------------------------------------------------------
@router.put("/rutarol/{id_ruta}/{id_rol}")
async def reemplazar(id_ruta: int, id_rol: int, nueva: RutaRolCrear):
    # La pareja de la URL es la que existe hoy; la del body, la que queda.
    try:
        await crear_servicio_rutarol().reemplazar(
            id_ruta, id_rol, nueva.fkidruta, nueva.fkidrol)
    except ValueError as exc:
        raise _error(400, "Solicitud invalida.", str(exc)) from exc
    except LookupError as exc:
        raise _error(404, "No encontrado.", str(exc)) from exc
    except ConflictoError as exc:
        raise _error(409, "La pareja nueva choca con los datos que ya "
                          "existen.", str(exc)) from exc
    except Exception as exc:
        raise _error(500, "Error interno.", str(exc)) from exc
    return {"mensaje": "Permiso movido.",
            "antes": {"fkidruta": id_ruta, "fkidrol": id_rol},
            "ahora": {"fkidruta": nueva.fkidruta, "fkidrol": nueva.fkidrol}}


# ----------------------------------------------------------------------
# PATCH /api/rutarol/{id_ruta}/{id_rol} — mover UN lado
# ----------------------------------------------------------------------
@router.patch("/rutarol/{id_ruta}/{id_rol}")
async def actualizar(id_ruta: int, id_rol: int, cambio: RutaRolActualizar):
    # Lo que no llega se conserva: `{"fkidrol": 3}` le pasa esta ruta a otro
    # rol y deja la ruta como estaba. Esa es toda la diferencia con el PUT.
    datos = cambio.model_dump(exclude_unset=True)
    if not datos:
        raise _error(400, "Solicitud invalida.",
                     "No se envio ningun lado para mover.")
    try:
        await crear_servicio_rutarol().reemplazar(
            id_ruta, id_rol,
            datos.get("fkidruta") or id_ruta,
            datos.get("fkidrol") or id_rol)
    except ValueError as exc:
        raise _error(400, "Solicitud invalida.", str(exc)) from exc
    except LookupError as exc:
        raise _error(404, "No encontrado.", str(exc)) from exc
    except ConflictoError as exc:
        raise _error(409, "La pareja nueva choca con los datos que ya "
                          "existen.", str(exc)) from exc
    except Exception as exc:
        raise _error(500, "Error interno.", str(exc)) from exc
    return {"mensaje": "Permiso actualizado.",
            "antes": {"fkidruta": id_ruta, "fkidrol": id_rol},
            "ahora": {"fkidruta": datos.get("fkidruta") or id_ruta,
                      "fkidrol": datos.get("fkidrol") or id_rol}}


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
