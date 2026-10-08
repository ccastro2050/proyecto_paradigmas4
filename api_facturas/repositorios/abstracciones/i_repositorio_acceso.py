"""
Contrato del repositorio de acceso — las DOS preguntas del control.

Es un repositorio nuevo y no un metodo mas en el de usuario, porque la
pregunta «puede este usuario entrar aqui?» no es del CRUD de usuario: es del
acceso. Cruza tres tablas y la responde un procedimiento.
"""

from typing import Protocol


class IRepositorioAcceso(Protocol):
    """Las 2 operaciones del control de acceso."""

    async def tiene_acceso(self, email: str, nombre_ruta: str) -> bool:
        """Tiene este correo acceso a esta ruta?

        Lo responde `verificar_acceso_ruta`, que YA EXISTE en la base de
        datos y cruza usuario -> rol_usuario -> rutarol. La API no arma ese
        JOIN: repetirlo en Python dejaria la regla en dos sitios.
        """
        ...

    async def rutas_permitidas(self, email: str) -> list[str]:
        """Las rutas a las que este correo SI puede entrar.

        Solo sirve para que la interfaz arme su menu. NO es el control de
        acceso: esconder una entrada del menu no protege nada, y quien
        escriba la direccion a mano entra igual si el servidor no comprueba.
        """
        ...
