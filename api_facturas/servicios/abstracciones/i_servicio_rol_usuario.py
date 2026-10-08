"""
Contrato del servicio de rol_usuario — la capa de NEGOCIO vista desde afuera.

El controller depende de esta interfaz, no de la clase concreta.
"""

from typing import Protocol


class IServicioRolUsuario(Protocol):
    """Las 7 operaciones de negocio del puente rol_usuario."""

    async def listar(self, limite: int) -> list[dict]:
        ...

    async def listar_por_usuario(self, fkemail: str) -> list[dict]:
        """Que roles tiene este usuario."""
        ...

    async def listar_por_rol(self, fkidrol: int) -> list[dict]:
        """Que usuarios tienen este rol."""
        ...

    async def crear(self, fkemail: str, fkidrol: int) -> None:
        """Da el rol al usuario. Lanza ConflictoError si ya lo tenia."""
        ...

    async def eliminar(self, fkemail: str, fkidrol: int) -> int:
        """Devuelve filas eliminadas (0 = no tenia ese rol)."""
        ...

    async def reemplazar(self, email_viejo: str, rol_viejo: int,
                         email_nuevo: str, rol_nuevo: int) -> int:
        """Mueve la pareja. Lanza LookupError si la vieja no existe."""
        ...

    async def reemplazar_roles(self, fkemail: str,
                               ids_rol: list[int]) -> dict:
        """Deja al usuario con EXACTAMENTE esos roles.

        Lanza LookupError si el usuario no existe —lo decide el
        procedimiento de la base de datos, no este codigo—.
        """
        ...
