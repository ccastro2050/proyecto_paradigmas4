"""
Controller de persona — la capa HTTP (v2). CALCADO del de producto:
traduce peticiones → servicio y excepciones de negocio → códigos.
"""

from fastapi import (APIRouter, Depends, HTTPException,
                     Response)

from autorizacion.dependencias import exige_permiso
from models.persona import Persona, PersonaActualizar, PersonaReemplazo
from servicios.ensamblador import crear_servicio_persona

# ----------------------------------------------------------------------
# LA GUARDIA, en el router y no en cada endpoint (v3)
# ----------------------------------------------------------------------
# `exige_permiso` corre ANTES del cuerpo de CUALQUIER endpoint de este
# archivo, y por dentro hace dos preguntas: hay token valido? (si no, 401) y
# tiene este correo la ruta «/persona»? (si no, 403). La consulta la responde
# `verificar_acceso_ruta`, en la base de datos, EN CADA PETICION.
#
# Va en el router a proposito: asi un endpoint nuevo en este archivo nace
# protegido. Endpoint por endpoint, el dia que alguien agregue uno y se le
# olvide, queda abierto —y nadie lo nota, porque funciona—.
router = APIRouter(prefix="/api", tags=["Persona"],
                   dependencies=[Depends(exige_permiso("/persona"))])


def _error(estado: int, mensaje: str, detalle: str) -> HTTPException:
    return HTTPException(
        status_code=estado,
        detail={"estado": estado, "mensaje": mensaje, "detalle": detalle},
    )


@router.get("/persona")
async def listar_personas(limite: int = 1000):
    try:
        servicio = crear_servicio_persona()
        filas = await servicio.listar(limite)
        if not filas:
            return Response(status_code=204)
        return {"tabla": "persona", "limite": limite,
                "total": len(filas), "datos": filas}
    except ValueError as excepcion:
        raise _error(400, "Parámetros inválidos.", str(excepcion))
    except Exception as excepcion:
        raise _error(500, "Error al consultar personas.", str(excepcion))


@router.get("/persona/{codigo}")
async def obtener_persona(codigo: str):
    try:
        servicio = crear_servicio_persona()
        return await servicio.obtener(codigo)
    except ValueError as excepcion:
        raise _error(400, "Parámetros inválidos.", str(excepcion))
    except LookupError as excepcion:
        raise _error(404, "Persona no encontrada.", str(excepcion))
    except Exception as excepcion:
        raise _error(500, "Error al consultar la persona.", str(excepcion))


@router.post("/persona")
async def crear_persona(modelo: Persona):
    try:
        servicio = crear_servicio_persona()
        await servicio.crear(modelo.model_dump())
        return {"estado": 200, "mensaje": "Persona creada exitosamente."}
    except ValueError as excepcion:
        raise _error(400, "Datos inválidos.", str(excepcion))
    except Exception as excepcion:
        # Aquí caen la PK duplicada y las FK: el motor viaja en `detalle`.
        raise _error(500, "No se pudo crear la persona.", str(excepcion))


@router.put("/persona/{codigo}")
async def reemplazar_persona(codigo: str, modelo: PersonaReemplazo):
    try:
        servicio = crear_servicio_persona()
        filas = await servicio.actualizar(codigo, modelo.model_dump())
        return {"estado": 200, "mensaje": "Persona reemplazada exitosamente.",
                "filasAfectadas": filas}
    except ValueError as excepcion:
        raise _error(400, "Parámetros inválidos.", str(excepcion))
    except LookupError as excepcion:
        raise _error(404, "Persona no encontrada.", str(excepcion))
    except Exception as excepcion:
        raise _error(500, "No se pudo reemplazar la persona.", str(excepcion))


@router.patch("/persona/{codigo}")
async def actualizar_persona(codigo: str, modelo: PersonaActualizar):
    try:
        servicio = crear_servicio_persona()
        datos = modelo.model_dump(exclude_none=True)
        filas = await servicio.actualizar(codigo, datos)
        return {"estado": 200, "mensaje": "Persona actualizada exitosamente.",
                "filasAfectadas": filas}
    except ValueError as excepcion:
        raise _error(400, "Parámetros inválidos.", str(excepcion))
    except LookupError as excepcion:
        raise _error(404, "Persona no encontrada.", str(excepcion))
    except Exception as excepcion:
        raise _error(500, "No se pudo actualizar la persona.", str(excepcion))


@router.delete("/persona/{codigo}")
async def eliminar_persona(codigo: str):
    try:
        servicio = crear_servicio_persona()
        filas = await servicio.eliminar(codigo)
        return {"estado": 200, "mensaje": "Persona eliminada exitosamente.",
                "filasEliminadas": filas}
    except ValueError as excepcion:
        raise _error(400, "Parámetros inválidos.", str(excepcion))
    except LookupError as excepcion:
        raise _error(404, "Persona no encontrada.", str(excepcion))
    except Exception as excepcion:
        raise _error(500, "No se pudo eliminar la persona.", str(excepcion))
