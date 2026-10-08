"""
Controller de usuario — la capa HTTP.

Traduccion de excepciones (ver 6_contracts.md):
    body invalido        -> 422 (Pydantic: email mal formado, clave corta)
    ValueError           -> 400 (validacion de negocio)
    LookupError          -> 404 (el email no existe)
    ConflictoError       -> 409 (el email ya existe)
    cualquier otra       -> 500 (error del motor)

Un detalle de rutas de FastAPI que muerde aqui: el email va en la URL y
contiene un punto, y `/api/usuario/verificar-contrasena` tambien encajaria
en `/api/usuario/{email}`. FastAPI resuelve por ORDEN DE DECLARACION, asi
que la ruta fija se declara ANTES de la ruta con parametro. Al revés, la
peticion de verificar acabaria buscando un usuario llamado
«verificar-contrasena» y devolveria 404.
"""

from fastapi import (APIRouter, Depends, HTTPException,
                     Response)

from autorizacion.dependencias import exige_permiso
from excepciones import ConflictoError
from models.usuario import (UsuarioActualizar, UsuarioCrear, UsuarioReemplazo,
                            VerificarContrasena)
from servicios.ensamblador import crear_servicio_usuario

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
router = APIRouter(prefix="/api", tags=["Usuario"],
                   dependencies=[Depends(exige_permiso("/usuario"))])


def _error(estado: int, mensaje: str, detalle: str) -> HTTPException:
    """Arma el sobre de error uniforme {estado, mensaje, detalle}."""
    return HTTPException(
        status_code=estado,
        detail={"estado": estado, "mensaje": mensaje, "detalle": detalle},
    )


# ----------------------------------------------------------------------
# GET /api/usuario — Listar (solo emails)
# ----------------------------------------------------------------------
@router.get("/usuario")
async def listar(limite: int = 1000):
    try:
        datos = await crear_servicio_usuario().listar(limite)
    except Exception as exc:
        raise _error(500, "Error interno.", str(exc)) from exc
    return {"tabla": "usuario", "limite": limite, "total": len(datos),
            "datos": datos}


# ----------------------------------------------------------------------
# POST /api/usuario/verificar-contrasena — comprobar sin entrar
# (VA ANTES de /usuario/{email}: ver el encabezado)
# ----------------------------------------------------------------------
@router.post("/usuario/verificar-contrasena")
async def verificar_contrasena(peticion: VerificarContrasena):
    try:
        coincide = await crear_servicio_usuario().verificar_contrasena(
            peticion.email, peticion.contrasena)
    except ValueError as exc:
        raise _error(400, "Solicitud invalida.", str(exc)) from exc
    except LookupError as exc:
        raise _error(404, "No encontrado.", str(exc)) from exc
    except Exception as exc:
        raise _error(500, "Error interno.", str(exc)) from exc
    if not coincide:
        # 401: se sabe quien dice ser, y la prueba no cuadra.
        raise _error(401, "Credenciales invalidas.",
                     "La contrasena no coincide.")
    return {"mensaje": "La contrasena coincide.", "email": peticion.email}


# ----------------------------------------------------------------------
# POST /api/usuario — Crear
# ----------------------------------------------------------------------
@router.post("/usuario", status_code=201)
async def crear(usuario: UsuarioCrear):
    try:
        await crear_servicio_usuario().crear(usuario.email, usuario.contrasena)
    except ValueError as exc:
        raise _error(400, "Solicitud invalida.", str(exc)) from exc
    except ConflictoError as exc:
        raise _error(409, "El usuario ya existe.", str(exc)) from exc
    except Exception as exc:
        raise _error(500, "Error interno.", str(exc)) from exc
    # La respuesta NO devuelve la contrasena, ni en hash.
    return {"mensaje": "Usuario creado.", "email": usuario.email}


# ----------------------------------------------------------------------
# GET /api/usuario/{email} — Obtener uno
# ----------------------------------------------------------------------
@router.get("/usuario/{email}")
async def obtener(email: str):
    try:
        return await crear_servicio_usuario().obtener(email)
    except ValueError as exc:
        raise _error(400, "Solicitud invalida.", str(exc)) from exc
    except LookupError as exc:
        raise _error(404, "No encontrado.", str(exc)) from exc
    except Exception as exc:
        raise _error(500, "Error interno.", str(exc)) from exc


# ----------------------------------------------------------------------
# PUT /api/usuario/{email} — Reemplazo COMPLETO (la contrasena)
# ----------------------------------------------------------------------
@router.put("/usuario/{email}")
async def reemplazar(email: str, usuario: UsuarioReemplazo):
    try:
        filas = await crear_servicio_usuario().actualizar_contrasena(
            email, usuario.contrasena)
    except ValueError as exc:
        raise _error(400, "Solicitud invalida.", str(exc)) from exc
    except Exception as exc:
        raise _error(500, "Error interno.", str(exc)) from exc
    if filas == 0:
        raise _error(404, "No encontrado.", f"El usuario {email} no existe.")
    return {"mensaje": "Contrasena reemplazada.", "email": email}


# ----------------------------------------------------------------------
# PATCH /api/usuario/{email} — Actualizacion PARCIAL
# ----------------------------------------------------------------------
@router.patch("/usuario/{email}")
async def actualizar(email: str, usuario: UsuarioActualizar):
    try:
        filas = await crear_servicio_usuario().actualizar_contrasena(
            email, usuario.contrasena)
    except ValueError as exc:
        raise _error(400, "Solicitud invalida.", str(exc)) from exc
    except Exception as exc:
        raise _error(500, "Error interno.", str(exc)) from exc
    if filas == 0:
        raise _error(404, "No encontrado.", f"El usuario {email} no existe.")
    return {"mensaje": "Contrasena actualizada.", "email": email}


# ----------------------------------------------------------------------
# DELETE /api/usuario/{email} — Eliminar
# ----------------------------------------------------------------------
@router.delete("/usuario/{email}", status_code=204)
async def eliminar(email: str):
    try:
        filas = await crear_servicio_usuario().eliminar(email)
    except ValueError as exc:
        raise _error(400, "Solicitud invalida.", str(exc)) from exc
    except Exception as exc:
        # Si el usuario todavia tiene roles, la FK de rol_usuario rechaza el
        # DELETE y esto es un 500: el cliente pidio algo que la base de datos
        # no permite todavia. Primero se le quitan los roles.
        raise _error(500, "Error interno.", str(exc)) from exc
    if filas == 0:
        raise _error(404, "No encontrado.", f"El usuario {email} no existe.")
    return Response(status_code=204)
