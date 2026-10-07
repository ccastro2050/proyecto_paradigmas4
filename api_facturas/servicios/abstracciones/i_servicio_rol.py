"""
Contrato del servicio de rol — la capa de NEGOCIO vista desde afuera.

El controller depende de esta interfaz, no de la clase concreta: asi se
puede probar la capa HTTP con un servicio falso, sin base de datos.
"""

from typing import Protocol


class IServicioRol(Protocol):
    """Las 5 operaciones de negocio de la entidad rol."""

    async def listar(self, limite: int) -> list[dict]:
        ...

    async def obtener(self, id_rol: int) -> dict:
        """Devuelve el rol. Lanza LookupError si no existe."""
        ...

    async def crear(self, datos: dict) -> None:
        """Inserta un rol. Lanza ValueError si el nombre no sirve."""
        ...

    async def actualizar(self, id_rol: int, datos: dict) -> int:
        """Devuelve filas afectadas (0 = no existe)."""
        ...

    async def eliminar(self, id_rol: int) -> int:
        """Devuelve filas eliminadas (0 = no existia)."""
        ...
