"""
Ensamblador — desde la v3, LA FÁBRICA REAL de repositorios.

La promesa de la v1 se paga aquí: llegó el segundo motor y SOLO este
archivo cambió de forma — controllers y servicios ni se enteraron (las
funciones crear_servicio_x conservan su firma).

El patrón: un diccionario proveedor → {cadena, familia de repositorios}.
UN punto del código decide el motor (DB_PROVIDER). La v4 pagó la cuenta
didáctica: agregar SQL Server costó exactamente UN bloque en _FABRICAS
(y sus imports) — ni un if regado por el código, ni un cambio arriba.
(El gemelo C# del curso escribe este mismo patrón con clases fábrica GoF:
compárelos — misma idea, dos idiomas.)
"""

import os

from repositorios.repositorio_cliente_mariadb import RepositorioClienteMariaDB
from repositorios.repositorio_cliente_postgresql import (
    RepositorioClientePostgreSQL,
)
from repositorios.repositorio_empresa_mariadb import RepositorioEmpresaMariaDB
from repositorios.repositorio_empresa_postgresql import (
    RepositorioEmpresaPostgreSQL,
)
from repositorios.repositorio_cliente_sqlserver import RepositorioClienteSqlServer
from repositorios.repositorio_empresa_sqlserver import RepositorioEmpresaSqlServer
from repositorios.repositorio_factura_mariadb import RepositorioFacturaMariaDB
from repositorios.repositorio_factura_sqlserver import RepositorioFacturaSqlServer
from repositorios.repositorio_factura_postgresql import (
    RepositorioFacturaPostgreSQL,
)
from repositorios.repositorio_persona_mariadb import RepositorioPersonaMariaDB
from repositorios.repositorio_persona_sqlserver import RepositorioPersonaSqlServer
from repositorios.repositorio_persona_postgresql import (
    RepositorioPersonaPostgreSQL,
)
from repositorios.repositorio_producto_mariadb import RepositorioProductoMariaDB
from repositorios.repositorio_producto_sqlserver import RepositorioProductoSqlServer
from repositorios.repositorio_producto_postgresql import (
    RepositorioProductoPostgreSQL,
)
from repositorios.repositorio_vendedor_mariadb import RepositorioVendedorMariaDB
from repositorios.repositorio_vendedor_sqlserver import RepositorioVendedorSqlServer
from repositorios.repositorio_vendedor_postgresql import (
    RepositorioVendedorPostgreSQL,
)
from servicios.abstracciones.i_servicio_cliente import IServicioCliente
from servicios.abstracciones.i_servicio_empresa import IServicioEmpresa
from servicios.abstracciones.i_servicio_factura import IServicioFactura
from servicios.abstracciones.i_servicio_persona import IServicioPersona
from servicios.abstracciones.i_servicio_producto import IServicioProducto
from servicios.abstracciones.i_servicio_vendedor import IServicioVendedor
from servicios.servicio_cliente import ServicioCliente
from servicios.servicio_empresa import ServicioEmpresa
from servicios.servicio_factura import ServicioFactura
from servicios.servicio_persona import ServicioPersona
from servicios.servicio_producto import ServicioProducto
from servicios.servicio_vendedor import ServicioVendedor

# ----------------------------------------------------------------------
# LA FÁBRICA: cada proveedor declara su cadena y su FAMILIA COMPLETA.
# Agregar un motor = agregar un bloque aquí. Nada más se toca.
# ----------------------------------------------------------------------
_FABRICAS = {
    "postgres": {
        "variable_cadena": "DB_POSTGRES",
        "repositorios": {
            "producto": RepositorioProductoPostgreSQL,
            "persona": RepositorioPersonaPostgreSQL,
            "empresa": RepositorioEmpresaPostgreSQL,
            "cliente": RepositorioClientePostgreSQL,
            "vendedor": RepositorioVendedorPostgreSQL,
            "factura": RepositorioFacturaPostgreSQL,
        },
    },
    "mariadb": {
        "variable_cadena": "DB_MARIADB",
        "repositorios": {
            "producto": RepositorioProductoMariaDB,
            "persona": RepositorioPersonaMariaDB,
            "empresa": RepositorioEmpresaMariaDB,
            "cliente": RepositorioClienteMariaDB,
            "vendedor": RepositorioVendedorMariaDB,
            "factura": RepositorioFacturaMariaDB,
        },
    },
    # v4 — el tercer motor: ESTE bloque es todo lo que costó agregarlo.
    "sqlserver": {
        "variable_cadena": "DB_SQLSERVER",
        "repositorios": {
            "producto": RepositorioProductoSqlServer,
            "persona": RepositorioPersonaSqlServer,
            "empresa": RepositorioEmpresaSqlServer,
            "cliente": RepositorioClienteSqlServer,
            "vendedor": RepositorioVendedorSqlServer,
            "factura": RepositorioFacturaSqlServer,
        },
    },
}


def proveedor_actual() -> str:
    """El motor activo según DB_PROVIDER (default: postgres)."""
    return os.environ.get("DB_PROVIDER", "postgres")


def _crear_repositorio(entidad: str):
    """El ÚNICO punto del sistema que decide el motor."""
    proveedor = proveedor_actual()
    if proveedor not in _FABRICAS:
        raise ValueError(
            f"DB_PROVIDER inválido: '{proveedor}' "
            f"(use uno de: {', '.join(sorted(_FABRICAS))})")
    fabrica = _FABRICAS[proveedor]
    clase = fabrica["repositorios"][entidad]
    # Construir un repositorio NO abre conexiones (solo guarda la cadena):
    return clase(os.environ[fabrica["variable_cadena"]])


# ----------------------------------------------------------------------
# Las funciones que usan los controllers — MISMA firma desde la v1/v2:
# los controllers no saben que ahora hay una fábrica detrás.
# ----------------------------------------------------------------------

def crear_servicio_producto() -> IServicioProducto:
    """Arma el servicio de producto con el repositorio del motor activo."""
    return ServicioProducto(_crear_repositorio("producto"))


def crear_servicio_persona() -> IServicioPersona:
    """Arma el servicio de persona con el repositorio del motor activo."""
    return ServicioPersona(_crear_repositorio("persona"))


def crear_servicio_empresa() -> IServicioEmpresa:
    """Arma el servicio de empresa con el repositorio del motor activo."""
    return ServicioEmpresa(_crear_repositorio("empresa"))


def crear_servicio_cliente() -> IServicioCliente:
    """Arma el servicio de cliente con el repositorio del motor activo."""
    return ServicioCliente(_crear_repositorio("cliente"))


def crear_servicio_vendedor() -> IServicioVendedor:
    """Arma el servicio de vendedor con el repositorio del motor activo."""
    return ServicioVendedor(_crear_repositorio("vendedor"))


def crear_servicio_factura() -> IServicioFactura:
    """Arma el servicio de factura con el repositorio del motor activo."""
    return ServicioFactura(_crear_repositorio("factura"))
