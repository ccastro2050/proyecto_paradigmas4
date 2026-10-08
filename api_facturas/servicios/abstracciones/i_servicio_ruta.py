"""
Contrato del servicio de ruta — la capa de NEGOCIO vista desde afuera.

El controller depende de esta interfaz, no de la clase concreta: asi se
puede probar la capa HTTP con un servicio falso, sin base de datos.
"""

from typing import Protocol


class IServicioRuta(Protocol):
    """Las 5 operaciones de negocio de la entidad ruta."""

    async def listar(self, limite: int) -> list[dict]:
        ...

    async def obtener(self, id_ruta: int) -> dict:
        """Devuelve la ruta. Lanza LookupError si no existe."""
        ...

    async def crear(self, datos: dict) -> None:
        """Inserta una ruta. Lanza ValueError si los datos no sirven."""
        ...

    async def actualizar(self, id_ruta: int, datos: dict) -> int:
        """Devuelve filas afectadas (0 = no existe)."""
        ...

    async def eliminar(self, id_ruta: int) -> int:
        """Devuelve filas eliminadas (0 = no existia)."""
        ...
