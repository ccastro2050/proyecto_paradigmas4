"""
Controller de rol — la capa HTTP.

Su unico trabajo es traducir: peticiones HTTP -> llamadas al servicio, y
excepciones de negocio -> codigos de estado. NO toca SQL ni reglas.

Traduccion de excepciones (ver 6_contracts.md):
    body invalido        -> 422 (lo produce Pydantic solo, antes de llegar aqui)
    ValueError           -> 400 (validacion de negocio)
    LookupError          -> 404 (el id no existe)
    cualquier otra       -> 500 (error del motor: BD caida, FK violada...)
"""

from fastapi import (APIRouter, Depends, HTTPException,
                     Response)

from autorizacion.dependencias import exige_permiso
from models.rol import Rol, RolActualizar, RolReemplazo
from servicios.ensamblador import crear_servicio_rol

# ----------------------------------------------------------------------
# LA GUARDIA, en el router y no en cada endpoint (v3)
# ----------------------------------------------------------------------
# `exige_permiso` corre ANTES del cuerpo de CUALQUIER endpoint de este
# archivo, y por dentro hace dos preguntas: hay token valido? (si no, 401) y
# tiene este correo la ruta «/rol»? (si no, 403). La consulta la responde
# `verificar_acceso_ruta`, en la base de datos, EN CADA PETICION.
#
# Va en el router a proposito: asi un endpoint nuevo en este archivo nace
# protegido. Endpoint por endpoint, el dia que alguien agregue uno y se le
# olvide, queda abierto —y nadie lo nota, porque funciona—.
router = APIRouter(prefix="/api", tags=["Rol"],
                   dependencies=[Depends(exige_permiso("/rol"))])


def _error(estado: int, mensaje: str, detalle: str) -> HTTPException:
    """Arma el sobre de error uniforme {estado, mensaje, detalle}."""
    return HTTPException(
        status_code=estado,
        detail={"estado": estado, "mensaje": mensaje, "detalle": detalle},
    )


# ----------------------------------------------------------------------
# GET /api/rol — Listar (query string ?limite=N)
# ----------------------------------------------------------------------
@router.get("/rol")
async def listar(limite: int = 1000):
    try:
        datos = await crear_servicio_rol().listar(limite)
    except Exception as exc:
        raise _error(500, "Error interno.", str(exc)) from exc
    # El SOBRE: nunca una lista pelada. Una lista suelta no puede decir
    # cuantos hay ni de que tabla viene.
    return {"tabla": "rol", "limite": limite, "total": len(datos), "datos": datos}


# ----------------------------------------------------------------------
# GET /api/rol/{id_rol} — Obtener uno
# ----------------------------------------------------------------------
@router.get("/rol/{id_rol}")
async def obtener(id_rol: int):
    try:
        return await crear_servicio_rol().obtener(id_rol)
    except LookupError as exc:
        raise _error(404, "No encontrado.", str(exc)) from exc
    except Exception as exc:
        raise _error(500, "Error interno.", str(exc)) from exc


# ----------------------------------------------------------------------
# POST /api/rol — Crear (el id lo genera la base de datos)
# ----------------------------------------------------------------------
@router.post("/rol", status_code=201)
async def crear(rol: Rol):
    try:
        await crear_servicio_rol().crear(rol.model_dump())
    except ValueError as exc:
        raise _error(400, "Solicitud invalida.", str(exc)) from exc
    except Exception as exc:
        raise _error(500, "Error interno.", str(exc)) from exc
    return {"mensaje": "Rol creado.", "nombre": rol.nombre}


# ----------------------------------------------------------------------
# PUT /api/rol/{id_rol} — Reemplazo COMPLETO
# ----------------------------------------------------------------------
@router.put("/rol/{id_rol}")
async def reemplazar(id_rol: int, rol: RolReemplazo):
    try:
        filas = await crear_servicio_rol().actualizar(id_rol, rol.model_dump())
    except ValueError as exc:
        raise _error(400, "Solicitud invalida.", str(exc)) from exc
    except Exception as exc:
        raise _error(500, "Error interno.", str(exc)) from exc
    if filas == 0:
        raise _error(404, "No encontrado.", f"El rol {id_rol} no existe.")
    return {"mensaje": "Rol reemplazado.", "id": id_rol}


# ----------------------------------------------------------------------
# PATCH /api/rol/{id_rol} — Actualizacion PARCIAL
# ----------------------------------------------------------------------
@router.patch("/rol/{id_rol}")
async def actualizar(id_rol: int, rol: RolActualizar):
    # exclude_unset: solo lo que el cliente ENVIO. Sin esto, un PATCH con
    # solo el nombre pondria los demas campos en None.
    datos = rol.model_dump(exclude_unset=True)
    try:
        filas = await crear_servicio_rol().actualizar(id_rol, datos)
    except ValueError as exc:
        raise _error(400, "Solicitud invalida.", str(exc)) from exc
    except Exception as exc:
        raise _error(500, "Error interno.", str(exc)) from exc
    if filas == 0:
        raise _error(404, "No encontrado.", f"El rol {id_rol} no existe.")
    return {"mensaje": "Rol actualizado.", "id": id_rol}


# ----------------------------------------------------------------------
# DELETE /api/rol/{id_rol} — Eliminar
# ----------------------------------------------------------------------
@router.delete("/rol/{id_rol}", status_code=204)
async def eliminar(id_rol: int):
    try:
        filas = await crear_servicio_rol().eliminar(id_rol)
    except Exception as exc:
        raise _error(500, "Error interno.", str(exc)) from exc
    if filas == 0:
        raise _error(404, "No encontrado.", f"El rol {id_rol} no existe.")
    return Response(status_code=204)
