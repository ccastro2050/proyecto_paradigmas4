"""
Controller de producto — la capa HTTP de la v1.

Su único trabajo es traducir: peticiones HTTP → llamadas al servicio, y
excepciones de negocio → códigos de estado. NO toca SQL ni reglas de negocio.

Traducción de excepciones (ver 6_contracts.md):
    body inválido        → 422 (lo produce Pydantic solo, antes de llegar aquí)
    ValueError           → 400 (validación de negocio)
    LookupError          → 404 (el código no existe)
    cualquier otra       → 500 (error del motor: PK duplicada, BD caída…)
"""

from fastapi import (APIRouter, Depends, HTTPException,
                     Response)

from autorizacion.dependencias import exige_permiso
from models.producto import Producto, ProductoActualizar, ProductoReemplazo
from servicios.ensamblador import crear_servicio_producto

# ----------------------------------------------------------------------
# LA GUARDIA, en el router y no en cada endpoint (v3)
# ----------------------------------------------------------------------
# `exige_permiso` corre ANTES del cuerpo de CUALQUIER endpoint de este
# archivo, y por dentro hace dos preguntas: hay token valido? (si no, 401) y
# tiene este correo la ruta «/producto»? (si no, 403). La consulta la responde
# `verificar_acceso_ruta`, en la base de datos, EN CADA PETICION.
#
# Va en el router a proposito: asi un endpoint nuevo en este archivo nace
# protegido. Endpoint por endpoint, el dia que alguien agregue uno y se le
# olvide, queda abierto —y nadie lo nota, porque funciona—.
router = APIRouter(prefix="/api", tags=["Producto"],
                   dependencies=[Depends(exige_permiso("/producto"))])


def _error(estado: int, mensaje: str, detalle: str) -> HTTPException:
    """Arma el sobre de error uniforme {estado, mensaje, detalle}."""
    return HTTPException(
        status_code=estado,
        detail={"estado": estado, "mensaje": mensaje, "detalle": detalle},
    )


# ----------------------------------------------------------------------
# GET /api/producto — Listar (query string ?limite=N)
# ----------------------------------------------------------------------
@router.get("/producto")
async def listar_productos(limite: int = 1000):
    try:
        servicio = crear_servicio_producto()
        filas = await servicio.listar(limite)
        if not filas:
            # 204: éxito SIN contenido — "tabla vacía" no es un error.
            return Response(status_code=204)
        return {"tabla": "producto", "limite": limite,
                "total": len(filas), "datos": filas}
    except ValueError as excepcion:
        raise _error(400, "Parámetros inválidos.", str(excepcion))
    except Exception as excepcion:
        raise _error(500, "Error al consultar productos.", str(excepcion))


# ----------------------------------------------------------------------
# GET /api/producto/{codigo} — Obtener uno (parámetro de ruta)
# ----------------------------------------------------------------------
@router.get("/producto/{codigo}")
async def obtener_producto(codigo: str):
    try:
        servicio = crear_servicio_producto()
        return await servicio.obtener(codigo)
    except ValueError as excepcion:
        raise _error(400, "Parámetros inválidos.", str(excepcion))
    except LookupError as excepcion:
        raise _error(404, "Producto no encontrado.", str(excepcion))
    except Exception as excepcion:
        raise _error(500, "Error al consultar el producto.", str(excepcion))


# ----------------------------------------------------------------------
# POST /api/producto — Crear (body completo, validado por Pydantic)
# ----------------------------------------------------------------------
@router.post("/producto")
async def crear_producto(producto: Producto):
    try:
        servicio = crear_servicio_producto()
        await servicio.crear(producto.model_dump())
        return {"estado": 200, "mensaje": "Producto creado exitosamente."}
    except ValueError as excepcion:
        raise _error(400, "Datos inválidos.", str(excepcion))
    except Exception as excepcion:
        # Aquí cae la PK duplicada: el error del motor viaja en `detalle`.
        raise _error(500, "No se pudo crear el producto.", str(excepcion))


# ----------------------------------------------------------------------
# PUT /api/producto/{codigo} — Reemplazo COMPLETO (todos los campos)
# ----------------------------------------------------------------------
@router.put("/producto/{codigo}")
async def reemplazar_producto(codigo: str, producto: ProductoReemplazo):
    try:
        servicio = crear_servicio_producto()
        # PUT: el modelo exige TODOS los campos → se escriben los 3.
        filas = await servicio.actualizar(codigo, producto.model_dump())
        return {"estado": 200, "mensaje": "Producto reemplazado exitosamente.",
                "filasAfectadas": filas}
    except ValueError as excepcion:
        raise _error(400, "Parámetros inválidos.", str(excepcion))
    except LookupError as excepcion:
        raise _error(404, "Producto no encontrado.", str(excepcion))
    except Exception as excepcion:
        raise _error(500, "No se pudo reemplazar el producto.", str(excepcion))


# ----------------------------------------------------------------------
# PATCH /api/producto/{codigo} — Actualización PARCIAL (solo lo enviado)
# ----------------------------------------------------------------------
@router.patch("/producto/{codigo}")
async def actualizar_producto(codigo: str, producto: ProductoActualizar):
    try:
        servicio = crear_servicio_producto()
        # PATCH: solo los campos que el cliente envió (exclude_none).
        # Si no envió ninguno, el servicio responde con ValueError → 400.
        datos = producto.model_dump(exclude_none=True)
        filas = await servicio.actualizar(codigo, datos)
        return {"estado": 200, "mensaje": "Producto actualizado exitosamente.",
                "filasAfectadas": filas}
    except ValueError as excepcion:
        raise _error(400, "Parámetros inválidos.", str(excepcion))
    except LookupError as excepcion:
        raise _error(404, "Producto no encontrado.", str(excepcion))
    except Exception as excepcion:
        raise _error(500, "No se pudo actualizar el producto.", str(excepcion))


# ----------------------------------------------------------------------
# DELETE /api/producto/{codigo} — Eliminar
# ----------------------------------------------------------------------
@router.delete("/producto/{codigo}")
async def eliminar_producto(codigo: str):
    try:
        servicio = crear_servicio_producto()
        filas = await servicio.eliminar(codigo)
        return {"estado": 200, "mensaje": "Producto eliminado exitosamente.",
                "filasEliminadas": filas}
    except ValueError as excepcion:
        raise _error(400, "Parámetros inválidos.", str(excepcion))
    except LookupError as excepcion:
        raise _error(404, "Producto no encontrado.", str(excepcion))
    except Exception as excepcion:
        raise _error(500, "No se pudo eliminar el producto.", str(excepcion))
