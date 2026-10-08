"""
Servicio de rol_usuario — las REGLAS del segundo puente.

Es el gemelo de `servicio_rutarol`, con una diferencia que importa: uno de
los lados es un email, y un email hay que limpiarlo —espacios de sobra,
mayusculas de un copiar y pegar— antes de usarlo como llave. La base de
datos distingue mayusculas en un VARCHAR; el usuario que escribe su correo,
no.

Lo que este servicio NO hace, y conviene notarlo: no comprueba que el
usuario exista antes de llamar al procedimiento. Esa comprobacion ya esta
DENTRO de `actualizar_roles_usuario`, y repetirla aqui costaria un viaje
mas a la base de datos para preguntar lo que el procedimiento pregunta de
todas formas. Confiar en la comprobacion que ya existe no es pereza: es no
tener dos sitios que pueden discrepar.
"""

from repositorios.abstracciones.i_repositorio_rol_usuario import (
    IRepositorioRolUsuario)


class ServicioRolUsuario:
    """Implementacion de IServicioRolUsuario."""

    def __init__(self, repositorio: IRepositorioRolUsuario):
        self._repositorio = repositorio

    @staticmethod
    def _validar_email(email: str) -> str:
        limpio = (email or "").strip().lower()
        if not limpio:
            raise ValueError("El email no puede estar vacio.")
        return limpio

    @staticmethod
    def _validar_id(valor: int, nombre: str) -> int:
        if valor is None or valor <= 0:
            raise ValueError(f"El {nombre} debe ser un entero mayor que cero.")
        return valor

    async def listar(self, limite: int) -> list[dict]:
        return await self._repositorio.obtener_todos(limite)

    async def listar_por_usuario(self, fkemail: str) -> list[dict]:
        return await self._repositorio.obtener_por_usuario(
            self._validar_email(fkemail))

    async def listar_por_rol(self, fkidrol: int) -> list[dict]:
        self._validar_id(fkidrol, "id del rol")
        return await self._repositorio.obtener_por_rol(fkidrol)

    async def crear(self, fkemail: str, fkidrol: int) -> None:
        fkemail = self._validar_email(fkemail)
        self._validar_id(fkidrol, "id del rol")
        await self._repositorio.crear(fkemail, fkidrol)

    async def eliminar(self, fkemail: str, fkidrol: int) -> int:
        fkemail = self._validar_email(fkemail)
        self._validar_id(fkidrol, "id del rol")
        return await self._repositorio.eliminar(fkemail, fkidrol)

    async def reemplazar(self, email_viejo: str, rol_viejo: int,
                         email_nuevo: str, rol_nuevo: int) -> int:
        email_viejo = self._validar_email(email_viejo)
        email_nuevo = self._validar_email(email_nuevo)
        self._validar_id(rol_viejo, "id del rol actual")
        self._validar_id(rol_nuevo, "id del rol nuevo")
        if (email_viejo, rol_viejo) == (email_nuevo, rol_nuevo):
            # Mover algo a donde ya esta: nada que hacer, nada que reportar.
            return 1
        filas = await self._repositorio.reemplazar(
            email_viejo, rol_viejo, email_nuevo, rol_nuevo)
        if filas == 0:
            raise LookupError(
                f"El usuario {email_viejo} no tiene el rol {rol_viejo}.")
        return filas

    async def reemplazar_roles(self, fkemail: str,
                               ids_rol: list[int]) -> dict:
        fkemail = self._validar_email(fkemail)
        for id_rol in ids_rol:
            self._validar_id(id_rol, "id del rol")
        # Sin repetidos: dos casillas marcadas con el mismo rol harian
        # chocar la llave primaria dentro del procedimiento.
        sin_repetidos = list(dict.fromkeys(ids_rol))
        return await self._repositorio.reemplazar_roles(fkemail, sin_repetidos)
