"""
Contrato del repositorio de usuario — la abstraccion de la capa de datos.

Tiene SEIS metodos, uno mas que el molde: `verificar_contrasena`. Y esta
aqui —y no en el servicio— por una razon de diseno que conviene tener clara:

El hash es un DETALLE DE COMO SE PERSISTE el secreto. Quien decide guardar
bcrypt con costo 12 es la capa de datos; el negocio solo quiere saber si la
contrasena coincide. Si manana el hash cambia a argon2, cambia este
repositorio y nada mas.

Corolario: el hash NUNCA sale de esta capa. No hay un metodo
`obtener_hash()` a proposito — devolverlo seria repartir el secreto por toda
la aplicacion.
"""

from typing import Protocol


class IRepositorioUsuario(Protocol):
    """Las 6 operaciones de datos de la entidad usuario."""

    async def obtener_todos(self, limite: int) -> list[dict]:
        """Devuelve hasta `limite` usuarios: SOLO el email."""
        ...

    async def obtener_por_email(self, email: str) -> dict | None:
        """Devuelve {email} o None. Nunca la contrasena."""
        ...

    async def crear(self, email: str, contrasena: str) -> bool:
        """Inserta el usuario. Recibe la contrasena EN CLARO y la hashea."""
        ...

    async def actualizar_contrasena(self, email: str, contrasena: str) -> int:
        """Rehashea y escribe. Devuelve filas afectadas (0 = no existe)."""
        ...

    async def eliminar(self, email: str) -> int:
        """Elimina el usuario. Devuelve filas eliminadas."""
        ...

    async def verificar_contrasena(self, email: str,
                                   contrasena: str) -> bool | None:
        """True/False si coincide; None si el usuario no existe.

        Tres respuestas, no dos: «no coincide» (401) y «no existe» (404) son
        hechos distintos, y el servicio necesita poder separarlos.
        """
        ...
