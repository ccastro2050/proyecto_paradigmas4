"""
Contrato del repositorio de ruta — la abstraccion de la capa de datos.

Un Protocol dice QUE metodos debe tener, sin decir COMO ni CONTRA QUE motor.
Cualquier clase con estos cinco cumple el contrato SIN heredar (tipado
estructural, PEP 544).

El servicio depende de ESTA interfaz, nunca de una clase concreta
—inversion de dependencias, la D de SOLID—.
"""

from typing import Protocol


class IRepositorioRuta(Protocol):
    """Las 5 operaciones de datos de la entidad ruta."""

    async def obtener_todos(self, limite: int) -> list[dict]:
        """Devuelve hasta `limite` rutas ordenadas por id."""
        ...

    async def obtener_por_id(self, id_ruta: int) -> dict | None:
        """Devuelve la ruta con ese id, o None si no existe."""
        ...

    async def crear(self, datos: dict) -> bool:
        """Inserta una ruta. Devuelve True si quedo insertada."""
        ...

    async def actualizar(self, id_ruta: int, datos: dict) -> int:
        """Escribe los campos de `datos` (los usan PUT y PATCH).

        Devuelve el numero de filas afectadas (0 = el id no existe).
        """
        ...

    async def eliminar(self, id_ruta: int) -> int:
        """Elimina la ruta. Devuelve filas eliminadas (0 = no existia)."""
        ...
