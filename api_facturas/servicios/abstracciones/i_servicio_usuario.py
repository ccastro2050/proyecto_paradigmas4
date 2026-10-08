"""
Contrato del servicio de usuario — la capa de NEGOCIO vista desde afuera.

El controller depende de esta interfaz, no de la clase concreta.
"""

from typing import Protocol


class IServicioUsuario(Protocol):
    """Las 6 operaciones de negocio de la entidad usuario."""

    async def listar(self, limite: int) -> list[dict]:
        ...

    async def obtener(self, email: str) -> dict:
        """Devuelve {email}. Lanza LookupError si no existe."""
        ...

    async def crear(self, email: str, contrasena: str) -> None:
        """Inserta el usuario. Lanza ConflictoError si el email ya existe."""
        ...

    async def actualizar_contrasena(self, email: str,
                                    contrasena: str | None) -> int:
        """Devuelve filas afectadas. Lanza ValueError si no llego nada."""
        ...

    async def eliminar(self, email: str) -> int:
        """Devuelve filas eliminadas (0 = no existia)."""
        ...

    async def verificar_contrasena(self, email: str, contrasena: str) -> bool:
        """True si coincide, False si no. LookupError si el usuario no existe."""
        ...
