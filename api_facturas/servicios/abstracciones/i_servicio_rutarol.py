"""
Contrato del servicio de rutarol — la capa de NEGOCIO vista desde afuera.

El controller depende de esta interfaz, no de la clase concreta.
"""

from typing import Protocol


class IServicioRutaRol(Protocol):
    """Las 7 operaciones de negocio del puente rutarol."""

    async def listar(self, limite: int) -> list[dict]:
        ...

    async def listar_por_ruta(self, fkidruta: int) -> list[dict]:
        """Que roles entran a esta ruta."""
        ...

    async def listar_por_rol(self, fkidrol: int) -> list[dict]:
        """A que rutas entra este rol."""
        ...

    async def crear(self, fkidruta: int, fkidrol: int) -> None:
        """Asigna el rol a la ruta. Lanza ConflictoError si ya estaba."""
        ...

    async def eliminar(self, fkidruta: int, fkidrol: int) -> int:
        """Devuelve filas eliminadas (0 = la pareja no existia)."""
        ...

    async def reemplazar(self, ruta_vieja: int, rol_viejo: int,
                         ruta_nueva: int, rol_nuevo: int) -> int:
        """Mueve el permiso. Lanza LookupError si la pareja vieja no existe."""
        ...

    async def reemplazar_de_rol(self, fkidrol: int,
                                ids_ruta: list[int]) -> int:
        """Deja al rol con EXACTAMENTE esas rutas. Devuelve cuantas quedaron."""
        ...
