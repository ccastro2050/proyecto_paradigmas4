"""
Punto de entrada de la API Facturas v4.

Crea la aplicación FastAPI, registra UN ROUTER POR RECURSO y expone el
endpoint de diagnóstico. Swagger queda en /docs y ReDoc en /redoc
(los defaults de FastAPI).

DOS ENDPOINTS ABIERTOS, TODO LO DEMÁS CON TOKEN
-----------------------------------------------
Desde la v3, cada router lleva su guardia —`exige_permiso`— y eso cierra la
API entera. Quedan abiertos exactamente dos, y los dos tienen por qué:

    GET  /                   el diagnóstico: un healthcheck no puede
                             necesitar credenciales para decir si hay vida
    POST /api/sesion/entrar  la puerta de la calle: no puede exigir el token
                             que ella misma entrega

Para probar con Swagger: entre por `/api/sesion/entrar`, copie el `token` de
la respuesta y péguelo en «Authorize» (arriba a la derecha) como
`Bearer <token>`.

Arranque:  uvicorn main:app --port 8005 --reload
Requiere:  la variable de entorno DB_POSTGRES (ver 7_quickstart.md).
"""

import os

from fastapi import FastAPI

from controllers.cliente_controller import router as router_cliente
from controllers.empresa_controller import router as router_empresa
from controllers.factura_controller import router as router_factura
from controllers.permisos_controller import router as router_permisos
from controllers.persona_controller import router as router_persona
from controllers.producto_controller import router as router_producto
from controllers.rol_controller import router as router_rol
from controllers.sesion_controller import router as router_sesion
from controllers.rol_usuario_controller import router as router_rol_usuario
from controllers.rutarol_controller import router as router_rutarol
from controllers.usuario_controller import router as router_usuario
from controllers.ruta_controller import router as router_ruta
from controllers.vendedor_controller import router as router_vendedor

app = FastAPI(
    title="API Facturas",
    version="v4",
    description="Once recursos —producto, persona, empresa, cliente, "
                "vendedor, factura maestro-detalle, rol, ruta, usuario y los "
                "dos puentes— con control de acceso: token en /api/sesion/"
                "entrar y permiso por ruta en cada peticion. El motor lo "
                "elige DB_PROVIDER: PostgreSQL, MariaDB o SQL Server.",
)

# La puerta de la calle y los permisos propios (v3):
app.include_router(router_sesion)
app.include_router(router_permisos)

# Un router por entidad — el molde de la v1, replicado (v2):
app.include_router(router_producto)
app.include_router(router_rol)
app.include_router(router_rol_usuario)
app.include_router(router_rutarol)
app.include_router(router_usuario)
app.include_router(router_ruta)
app.include_router(router_persona)
app.include_router(router_empresa)
app.include_router(router_cliente)
app.include_router(router_vendedor)
app.include_router(router_factura)


@app.get("/", tags=["Diagnóstico"])
async def diagnostico():
    """Confirma que la API está en línea (usable como healthcheck)."""
    return {"mensaje": "API Facturas funcionando", "version": "v4",
            # v3: a cuál motor le está hablando la API (el interruptor):
            "motor": os.environ.get("DB_PROVIDER", "postgres"),
            "documentacion": "/docs"}
