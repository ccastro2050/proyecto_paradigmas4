"""
Contrato del repositorio de rol — la abstraccion de la capa de datos.

Un Protocol dice QUE metodos debe tener, sin decir COMO ni CONTRA QUE motor.
Cualquier clase con estos cinco cumple el contrato SIN heredar (tipado
estructural, PEP 544): el de PostgreSQL, el de MariaDB, el de SQL Server, o
un falso en memoria para las pruebas.

El servicio depende de ESTA interfaz, nunca de una clase concreta
—inversion de dependencias, la D de SOLID—.
"""

from typing import Protocol


class IRepositorioRol(Protocol):
    """Las 5 operaciones de datos de la entidad rol."""

    async def obtener_todos(self, limite: int) -> list[dict]:
        """Devuelve hasta `limite` roles ordenados por id."""
        ...

    async def obtener_por_id(self, id_rol: int) -> dict | None:
        """Devuelve el rol con ese id, o None si no existe."""
        ...

    async def crear(self, datos: dict) -> bool:
        """Inserta un rol. Devuelve True si quedo insertado."""
        ...

    async def actualizar(self, id_rol: int, datos: dict) -> int:
        """Escribe los campos de `datos` (los usan PUT y PATCH).

        Devuelve el numero de filas afectadas (0 = el id no existe).
        """
        ...

    async def eliminar(self, id_rol: int) -> int:
        """Elimina el rol. Devuelve filas eliminadas (0 = no existia)."""
        ...
