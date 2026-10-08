"""
Contrato del repositorio de rol_usuario — el segundo puente.

Mismo patron que `rutarol`: dos busquedas por lado, el `eliminar` con las
dos columnas, y las dos operaciones transaccionales. Lo que cambia es el
tipo de un lado —el email es texto— y, sobre todo, COMO se implementa la
ultima:

`reemplazar_roles` no arma la transaccion en Python: llama al procedimiento
`actualizar_roles_usuario`, que ya existe en la base de datos y hace
exactamente eso. La regla que se aplica es simple y conviene recordarla:
**si la base de datos ya tiene el procedimiento, la API lo llama; si no lo
tiene, el repositorio abre su propia transaccion** —como en `rutarol`—.
Reescribir en Python algo que ya esta escrito en plpgsql deja dos verdades
que se pueden desincronizar.
"""

from typing import Protocol


class IRepositorioRolUsuario(Protocol):
    """Las 7 operaciones de datos del puente rol_usuario."""

    async def obtener_todos(self, limite: int) -> list[dict]:
        """Las parejas, con el nombre del rol."""
        ...

    async def obtener_por_usuario(self, fkemail: str) -> list[dict]:
        """Que roles tiene este usuario."""
        ...

    async def obtener_por_rol(self, fkidrol: int) -> list[dict]:
        """Que usuarios tienen este rol."""
        ...

    async def crear(self, fkemail: str, fkidrol: int) -> bool:
        """Inserta la pareja. Choca si ya existe (llave primaria)."""
        ...

    async def eliminar(self, fkemail: str, fkidrol: int) -> int:
        """Borra UNA pareja exacta: las dos columnas, no una."""
        ...

    async def reemplazar(self, email_viejo: str, rol_viejo: int,
                         email_nuevo: str, rol_nuevo: int) -> int:
        """MUEVE la pareja, en una transaccion. 0 = la vieja no existia."""
        ...

    async def reemplazar_roles(self, fkemail: str,
                               ids_rol: list[int]) -> dict:
        """Deja al usuario con EXACTAMENTE esos roles.

        Llama al procedimiento `actualizar_roles_usuario` y devuelve lo que
        el procedimiento responde: {email, roles}.
        """
        ...
