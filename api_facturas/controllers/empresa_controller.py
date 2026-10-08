"""
Controller de empresa — la capa HTTP (v2). CALCADO del de producto:
traduce peticiones → servicio y excepciones de negocio → códigos.
"""

from fastapi import (APIRouter, Depends, HTTPException,
                     Response)

from autorizacion.dependencias import exige_permiso
from models.empresa import Empresa, EmpresaActualizar, EmpresaReemplazo
from servicios.ensamblador import crear_servicio_empresa

# ----------------------------------------------------------------------
# LA GUARDIA, en el router y no en cada endpoint (v3)
# ----------------------------------------------------------------------
# `exige_permiso` corre ANTES del cuerpo de CUALQUIER endpoint de este
# archivo, y por dentro hace dos preguntas: hay token valido? (si no, 401) y
# tiene este correo la ruta «/empresa»? (si no, 403). La consulta la responde
# `verificar_acceso_ruta`, en la base de datos, EN CADA PETICION.
#
# Va en el router a proposito: asi un endpoint nuevo en este archivo nace
# protegido. Endpoint por endpoint, el dia que alguien agregue uno y se le
# olvide, queda abierto —y nadie lo nota, porque funciona—.
router = APIRouter(prefix="/api", tags=["Empresa"],
                   dependencies=[Depends(exige_permiso("/empresa"))])


def _error(estado: int, mensaje: str, detalle: str) -> HTTPException:
    return HTTPException(
        status_code=estado,
        detail={"estado": estado, "mensaje": mensaje, "detalle": detalle},
    )


@router.get("/empresa")
async def listar_empresas(limite: int = 1000):
    try:
        servicio = crear_servicio_empresa()
        filas = await servicio.listar(limite)
        if not filas:
            return Response(status_code=204)
        return {"tabla": "empresa", "limite": limite,
                "total": len(filas), "datos": filas}
    except ValueError as excepcion:
        raise _error(400, "Parámetros inválidos.", str(excepcion))
    except Exception as excepcion:
        raise _error(500, "Error al consultar empresas.", str(excepcion))


@router.get("/empresa/{codigo}")
async def obtener_empresa(codigo: str):
    try:
        servicio = crear_servicio_empresa()
        return await servicio.obtener(codigo)
    except ValueError as excepcion:
        raise _error(400, "Parámetros inválidos.", str(excepcion))
    except LookupError as excepcion:
        raise _error(404, "Empresa no encontrada.", str(excepcion))
    except Exception as excepcion:
        raise _error(500, "Error al consultar la empresa.", str(excepcion))


@router.post("/empresa")
async def crear_empresa(modelo: Empresa):
    try:
        servicio = crear_servicio_empresa()
        await servicio.crear(modelo.model_dump())
        return {"estado": 200, "mensaje": "Empresa creada exitosamente."}
    except ValueError as excepcion:
        raise _error(400, "Datos inválidos.", str(excepcion))
    except Exception as excepcion:
        # Aquí caen la PK duplicada y las FK: el motor viaja en `detalle`.
        raise _error(500, "No se pudo crear la empresa.", str(excepcion))


@router.put("/empresa/{codigo}")
async def reemplazar_empresa(codigo: str, modelo: EmpresaReemplazo):
    try:
        servicio = crear_servicio_empresa()
        filas = await servicio.actualizar(codigo, modelo.model_dump())
        return {"estado": 200, "mensaje": "Empresa reemplazada exitosamente.",
                "filasAfectadas": filas}
    except ValueError as excepcion:
        raise _error(400, "Parámetros inválidos.", str(excepcion))
    except LookupError as excepcion:
        raise _error(404, "Empresa no encontrada.", str(excepcion))
    except Exception as excepcion:
        raise _error(500, "No se pudo reemplazar la empresa.", str(excepcion))


@router.patch("/empresa/{codigo}")
async def actualizar_empresa(codigo: str, modelo: EmpresaActualizar):
    try:
        servicio = crear_servicio_empresa()
        datos = modelo.model_dump(exclude_none=True)
        filas = await servicio.actualizar(codigo, datos)
        return {"estado": 200, "mensaje": "Empresa actualizada exitosamente.",
                "filasAfectadas": filas}
    except ValueError as excepcion:
        raise _error(400, "Parámetros inválidos.", str(excepcion))
    except LookupError as excepcion:
        raise _error(404, "Empresa no encontrada.", str(excepcion))
    except Exception as excepcion:
        raise _error(500, "No se pudo actualizar la empresa.", str(excepcion))


@router.delete("/empresa/{codigo}")
async def eliminar_empresa(codigo: str):
    try:
        servicio = crear_servicio_empresa()
        filas = await servicio.eliminar(codigo)
        return {"estado": 200, "mensaje": "Empresa eliminada exitosamente.",
                "filasEliminadas": filas}
    except ValueError as excepcion:
        raise _error(400, "Parámetros inválidos.", str(excepcion))
    except LookupError as excepcion:
        raise _error(404, "Empresa no encontrada.", str(excepcion))
    except Exception as excepcion:
        raise _error(500, "No se pudo eliminar la empresa.", str(excepcion))
