"""
Controller de factura — la capa HTTP (v2).

Cuatro endpoints, sin PUT/PATCH/DELETE: las facturas se ANULAN (borrado
lógico), no se editan ni se borran por la API. La traducción de
excepciones crece una fila respecto de la v1:

    ValueError      → 400 · LookupError → 404
    ConflictoError  → 409 (ya estaba anulada)
    cualquier otra  → 500 (stock insuficiente del trigger, FK, BD caída…)
"""

from fastapi import (APIRouter, Depends, HTTPException,
                     Response)

from autorizacion.dependencias import exige_permiso
from excepciones import ConflictoError
from models.factura import FacturaCrear
from servicios.ensamblador import crear_servicio_factura

# ----------------------------------------------------------------------
# LA GUARDIA, en el router y no en cada endpoint (v3)
# ----------------------------------------------------------------------
# `exige_permiso` corre ANTES del cuerpo de CUALQUIER endpoint de este
# archivo, y por dentro hace dos preguntas: hay token valido? (si no, 401) y
# tiene este correo la ruta «/factura»? (si no, 403). La consulta la responde
# `verificar_acceso_ruta`, en la base de datos, EN CADA PETICION.
#
# Va en el router a proposito: asi un endpoint nuevo en este archivo nace
# protegido. Endpoint por endpoint, el dia que alguien agregue uno y se le
# olvide, queda abierto —y nadie lo nota, porque funciona—.
router = APIRouter(prefix="/api", tags=["Factura"],
                   dependencies=[Depends(exige_permiso("/factura"))])


def _error(estado: int, mensaje: str, detalle: str) -> HTTPException:
    return HTTPException(
        status_code=estado,
        detail={"estado": estado, "mensaje": mensaje, "detalle": detalle},
    )


# ----------------------------------------------------------------------
# GET /api/factura — Listar (SP listar: nombres y detalle adentro)
# ----------------------------------------------------------------------
@router.get("/factura")
async def listar_facturas():
    try:
        servicio = crear_servicio_factura()
        filas = await servicio.listar()
        if not filas:
            return Response(status_code=204)
        return {"tabla": "factura", "total": len(filas), "datos": filas}
    except Exception as excepcion:
        raise _error(500, "Error al consultar facturas.", str(excepcion))


# ----------------------------------------------------------------------
# GET /api/factura/{numero} — Consultar una (SP consultar)
# ----------------------------------------------------------------------
@router.get("/factura/{numero}")
async def consultar_factura(numero: int):
    try:
        servicio = crear_servicio_factura()
        return await servicio.consultar(numero)
    except ValueError as excepcion:
        raise _error(400, "Parámetros inválidos.", str(excepcion))
    except LookupError as excepcion:
        raise _error(404, "Factura no encontrada.", str(excepcion))
    except Exception as excepcion:
        raise _error(500, "Error al consultar la factura.", str(excepcion))


# ----------------------------------------------------------------------
# POST /api/factura — Crear (SP insertar; el trigger hace las cuentas)
# ----------------------------------------------------------------------
@router.post("/factura")
async def crear_factura(factura: FacturaCrear):
    try:
        servicio = crear_servicio_factura()
        resultado = await servicio.crear(
            factura.fkidcliente, factura.fkidvendedor,
            [renglon.model_dump() for renglon in factura.productos])
        return {"estado": 200, "mensaje": "Factura creada exitosamente.",
                "factura": resultado.get("factura"),
                "productos": resultado.get("productos")}
    except ValueError as excepcion:
        raise _error(400, "Datos inválidos.", str(excepcion))
    except Exception as excepcion:
        # Aquí caen el stock insuficiente (trigger) y las FK:
        raise _error(500, "No se pudo crear la factura.", str(excepcion))


# ----------------------------------------------------------------------
# POST /api/factura/{numero}/anular — Borrado LÓGICO (SP anular)
# ----------------------------------------------------------------------
@router.post("/factura/{numero}/anular")
async def anular_factura(numero: int):
    try:
        servicio = crear_servicio_factura()
        resultado = await servicio.anular(numero)
        return {"estado": 200, "mensaje": "Factura anulada exitosamente.",
                "resultado": resultado}
    except ValueError as excepcion:
        raise _error(400, "Parámetros inválidos.", str(excepcion))
    except LookupError as excepcion:
        raise _error(404, "Factura no encontrada.", str(excepcion))
    except ConflictoError as excepcion:
        raise _error(409, "La factura ya está anulada.", str(excepcion))
    except Exception as excepcion:
        raise _error(500, "No se pudo anular la factura.", str(excepcion))
