"""
Controller de ruta — la capa HTTP.

Su unico trabajo es traducir: peticiones HTTP -> llamadas al servicio, y
excepciones de negocio -> codigos de estado. NO toca SQL ni reglas.

Traduccion de excepciones (ver 6_contracts.md):
    body invalido        -> 422 (lo produce Pydantic solo, antes de llegar aqui)
    ValueError           -> 400 (validacion de negocio: la ruta sin barra)
    LookupError          -> 404 (el id no existe)
    ConflictoError       -> 409 (esa ruta ya existe: el UNIQUE)
    cualquier otra       -> 500 (error del motor: base de datos caida...)

El 409 es la fila nueva frente al molde de `rol`, y vale la pena ver por
que: 400 dice «lo que usted mando esta mal escrito» —se arregla cambiando
el texto—; 409 dice «lo que mando esta bien escrito, pero choca con lo que
ya hay» —se arregla mirando que existe—. Devolver 400 en los dos casos le
quita al cliente la informacion que necesita para reaccionar.
"""

from fastapi import (APIRouter, Depends, HTTPException,
                     Response)

from autorizacion.dependencias import exige_permiso
from excepciones import ConflictoError
from models.ruta import Ruta, RutaActualizar, RutaReemplazo
from servicios.ensamblador import crear_servicio_ruta

# ----------------------------------------------------------------------
# LA GUARDIA, en el router y no en cada endpoint (v3)
# ----------------------------------------------------------------------
# `exige_permiso` corre ANTES del cuerpo de CUALQUIER endpoint de este
# archivo, y por dentro hace dos preguntas: hay token valido? (si no, 401) y
# tiene este correo la ruta «/ruta»? (si no, 403). La consulta la responde
# `verificar_acceso_ruta`, en la base de datos, EN CADA PETICION.
#
# Va en el router a proposito: asi un endpoint nuevo en este archivo nace
# protegido. Endpoint por endpoint, el dia que alguien agregue uno y se le
# olvide, queda abierto —y nadie lo nota, porque funciona—.
router = APIRouter(prefix="/api", tags=["Ruta"],
                   dependencies=[Depends(exige_permiso("/ruta"))])


def _error(estado: int, mensaje: str, detalle: str) -> HTTPException:
    """Arma el sobre de error uniforme {estado, mensaje, detalle}."""
    return HTTPException(
        status_code=estado,
        detail={"estado": estado, "mensaje": mensaje, "detalle": detalle},
    )


# ----------------------------------------------------------------------
# GET /api/ruta — Listar (query string ?limite=N)
# ----------------------------------------------------------------------
@router.get("/ruta")
async def listar(limite: int = 1000):
    try:
        datos = await crear_servicio_ruta().listar(limite)
    except Exception as exc:
        raise _error(500, "Error interno.", str(exc)) from exc
    # El SOBRE: nunca una lista pelada. Una lista suelta no puede decir
    # cuantas hay ni de que tabla viene.
    return {"tabla": "ruta", "limite": limite, "total": len(datos),
            "datos": datos}


# ----------------------------------------------------------------------
# GET /api/ruta/{id_ruta} — Obtener una
# ----------------------------------------------------------------------
@router.get("/ruta/{id_ruta}")
async def obtener(id_ruta: int):
    try:
        return await crear_servicio_ruta().obtener(id_ruta)
    except LookupError as exc:
        raise _error(404, "No encontrado.", str(exc)) from exc
    except Exception as exc:
        raise _error(500, "Error interno.", str(exc)) from exc


# ----------------------------------------------------------------------
# POST /api/ruta — Crear (el id lo genera la base de datos)
# ----------------------------------------------------------------------
@router.post("/ruta", status_code=201)
async def crear(ruta: Ruta):
    try:
        await crear_servicio_ruta().crear(ruta.model_dump())
    except ValueError as exc:
        raise _error(400, "Solicitud invalida.", str(exc)) from exc
    except ConflictoError as exc:
        raise _error(409, "La ruta ya existe.", str(exc)) from exc
    except Exception as exc:
        raise _error(500, "Error interno.", str(exc)) from exc
    return {"mensaje": "Ruta creada.", "ruta": ruta.ruta}


# ----------------------------------------------------------------------
# PUT /api/ruta/{id_ruta} — Reemplazo COMPLETO
# ----------------------------------------------------------------------
@router.put("/ruta/{id_ruta}")
async def reemplazar(id_ruta: int, ruta: RutaReemplazo):
    try:
        filas = await crear_servicio_ruta().actualizar(id_ruta,
                                                       ruta.model_dump())
    except ValueError as exc:
        raise _error(400, "Solicitud invalida.", str(exc)) from exc
    except ConflictoError as exc:
        raise _error(409, "La ruta ya existe.", str(exc)) from exc
    except Exception as exc:
        raise _error(500, "Error interno.", str(exc)) from exc
    if filas == 0:
        raise _error(404, "No encontrado.", f"La ruta {id_ruta} no existe.")
    return {"mensaje": "Ruta reemplazada.", "id": id_ruta}


# ----------------------------------------------------------------------
# PATCH /api/ruta/{id_ruta} — Actualizacion PARCIAL
# ----------------------------------------------------------------------
@router.patch("/ruta/{id_ruta}")
async def actualizar(id_ruta: int, ruta: RutaActualizar):
    # exclude_unset: solo lo que el cliente ENVIO. Sin esto, un PATCH con
    # solo la descripcion pondria la ruta en None.
    datos = ruta.model_dump(exclude_unset=True)
    try:
        filas = await crear_servicio_ruta().actualizar(id_ruta, datos)
    except ValueError as exc:
        raise _error(400, "Solicitud invalida.", str(exc)) from exc
    except ConflictoError as exc:
        raise _error(409, "La ruta ya existe.", str(exc)) from exc
    except Exception as exc:
        raise _error(500, "Error interno.", str(exc)) from exc
    if filas == 0:
        raise _error(404, "No encontrado.", f"La ruta {id_ruta} no existe.")
    return {"mensaje": "Ruta actualizada.", "id": id_ruta}


# ----------------------------------------------------------------------
# DELETE /api/ruta/{id_ruta} — Eliminar
# ----------------------------------------------------------------------
@router.delete("/ruta/{id_ruta}", status_code=204)
async def eliminar(id_ruta: int):
    try:
        filas = await crear_servicio_ruta().eliminar(id_ruta)
    except Exception as exc:
        raise _error(500, "Error interno.", str(exc)) from exc
    if filas == 0:
        raise _error(404, "No encontrado.", f"La ruta {id_ruta} no existe.")
    return Response(status_code=204)
