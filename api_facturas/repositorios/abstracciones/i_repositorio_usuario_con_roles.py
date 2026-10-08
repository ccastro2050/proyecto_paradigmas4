"""
Contrato de datos de usuario-con-roles: CINCO operaciones, una por
procedimiento almacenado — ni una mas.

Es el segundo recurso de la API que no escribe SQL propio (el primero fue
factura). Y la comparacion entre los dos dice cuando vale la pena un
procedimiento:

    factura                 el maestro y su detalle, con disparador de
                            totales y stock: varias tablas, una transaccion
    usuario-con-roles       el usuario y sus roles: dos tablas, una
                            transaccion

Las dos veces el motivo es el mismo —VARIAS sentencias que tienen que valer
como una—, no «porque los procedimientos son rapidos».

LO QUE EL PROCEDIMIENTO NO SABE, y por eso lo hace el repositorio: el
procedimiento guarda la contrasena TAL CUAL se le entrega. El hash es cosa de
la capa de datos de la API, igual que en el repositorio de usuario. Si se le
pasara la contrasena en claro, quedaria en claro en la tabla.
"""

from typing import Protocol


class IRepositorioUsuarioConRoles(Protocol):
    """Las 5 operaciones, cada una un procedimiento."""

    async def listar(self) -> list[dict]:
        """`listar_usuarios_con_roles` — todos, con sus roles."""
        ...

    async def consultar(self, email: str) -> dict:
        """`consultar_usuario_con_roles` — uno. Lanza LookupError si no esta."""
        ...

    async def crear(self, email: str, contrasena: str,
                    ids_rol: list[int]) -> dict:
        """`crear_usuario_con_roles` — el usuario y sus roles, en una."""
        ...

    async def actualizar(self, email: str, contrasena: str | None,
                         ids_rol: list[int]) -> dict:
        """`actualizar_usuario_con_roles` — reemplaza roles y, si llega, clave."""
        ...

    async def eliminar(self, email: str) -> dict:
        """`eliminar_usuario_con_roles` — el usuario y sus asignaciones."""
        ...
