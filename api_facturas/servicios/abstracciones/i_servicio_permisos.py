"""
Contrato del servicio de permisos — lo que la interfaz necesita saber.

Un solo metodo, y conviene insistir en lo que NO es: esta lista no protege
nada. Sirve para dibujar un menu. La decision —si una operacion entra o
no— la toma `verificar_acceso_ruta` en cada peticion, y solo el.
"""

from typing import Protocol


class IServicioPermisos(Protocol):
    """La operacion de consulta de permisos propios."""

    async def mis_rutas(self, email: str) -> list[str]:
        """Las rutas a las que este correo puede entrar."""
        ...
