"""
Contrato del servicio de usuario-con-roles — la capa de NEGOCIO.

Cinco operaciones, las mismas cinco del repositorio. Y conviene explicar por
que existe esta capa si no hace mas que pasar la pelota: porque **aqui vive
la regla de que un usuario no se crea sin rol**. Esa regla no es del motor
—el procedimiento acepta una lista vacia sin chistar— ni de HTTP. Es del
dominio, y este es su sitio.
"""

from typing import Protocol


class IServicioUsuarioConRoles(Protocol):
    """Las 5 operaciones de negocio de usuario-con-roles."""

    async def listar(self) -> list[dict]:
        ...

    async def consultar(self, email: str) -> dict:
        """Lanza LookupError si el usuario no existe."""
        ...

    async def crear(self, email: str, contrasena: str,
                    ids_rol: list[int]) -> dict:
        """Lanza ValueError si no llega ningun rol, ConflictoError si ya existe."""
        ...

    async def actualizar(self, email: str, contrasena: str | None,
                         ids_rol: list[int]) -> dict:
        """Reemplaza los roles; la contrasena solo si llega."""
        ...

    async def actualizar_parcial(self, email: str, contrasena: str | None,
                                 ids_rol: list[int] | None) -> dict:
        """Lo del PATCH: cambia solo lo que llego.

        Si `ids_rol` es None, CONSERVA los roles que el usuario tiene hoy.
        """
        ...

    async def eliminar(self, email: str) -> dict:
        """Lanza LookupError si el usuario no existe."""
        ...
