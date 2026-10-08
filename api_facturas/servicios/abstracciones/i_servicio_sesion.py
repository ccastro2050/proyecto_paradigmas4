"""
Contrato del servicio de sesion — entrar y renovar.

Dos metodos, y los dos devuelven `dict | None`: la sesion o nada. Que ese
«nada» sea un 401 lo decide el controller; aqui no se sabe que existe HTTP.
"""

from typing import Protocol


class IServicioSesion(Protocol):
    """Las 2 operaciones de la sesion."""

    async def entrar(self, email: str, contrasena: str) -> dict | None:
        """La sesion {token, email, roles, expira}, o None si no cuadra."""
        ...

    async def renovar(self, email: str) -> dict | None:
        """Un token nuevo —con los roles de HOY— para quien ya tenia uno."""
        ...
