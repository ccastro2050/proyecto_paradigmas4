"""
Servicio de usuario-con-roles — donde viven las reglas que el motor no tiene.

Tres, y ninguna la impone la base de datos:

1. **Un usuario no se crea sin rol.** El procedimiento acepta una lista
   vacia; el negocio no, porque un usuario sin rol no puede hacer nada y solo
   deja basura en la tabla. Esto es 400, no 422: la peticion esta bien
   escrita, lo que pide es lo que no vale.

2. **La lista de roles no lleva repetidos.** Dos casillas marcadas con el
   mismo rol harian chocar la llave primaria dentro del procedimiento, con un
   500 que no es culpa de nadie. Se limpia aqui.

3. **Al no mandar contrasena, no se toca.** Se traduce a la convencion que
   el procedimiento ya tiene —cadena vacia es «dejela como esta»— y esa
   traduccion la hace el repositorio. Aqui solo se decide que `None` y `""`
   significan lo mismo.
"""

from repositorios.abstracciones.i_repositorio_usuario_con_roles import (
    IRepositorioUsuarioConRoles)


class ServicioUsuarioConRoles:
    """Implementacion de IServicioUsuarioConRoles."""

    def __init__(self, repositorio: IRepositorioUsuarioConRoles):
        self._repositorio = repositorio

    @staticmethod
    def _validar_email(email: str) -> str:
        limpio = (email or "").strip().lower()
        if not limpio:
            raise ValueError("El email no puede estar vacio.")
        return limpio

    @staticmethod
    def _validar_roles(ids_rol: list[int]) -> list[int]:
        """Al menos uno, sin repetidos, todos positivos."""
        limpios = []
        for id_rol in ids_rol or []:
            if int(id_rol) <= 0:
                raise ValueError(
                    "El id de un rol debe ser un entero mayor que cero.")
            if int(id_rol) not in limpios:
                limpios.append(int(id_rol))
        if not limpios:
            raise ValueError(
                "El usuario necesita al menos un rol: sin rol no puede hacer "
                "nada.")
        return limpios

    async def listar(self) -> list[dict]:
        return await self._repositorio.listar()

    async def consultar(self, email: str) -> dict:
        return await self._repositorio.consultar(self._validar_email(email))

    async def crear(self, email: str, contrasena: str,
                    ids_rol: list[int]) -> dict:
        return await self._repositorio.crear(
            self._validar_email(email), contrasena,
            self._validar_roles(ids_rol))

    async def actualizar(self, email: str, contrasena: str | None,
                         ids_rol: list[int]) -> dict:
        return await self._repositorio.actualizar(
            self._validar_email(email), contrasena or None,
            self._validar_roles(ids_rol))

    async def actualizar_parcial(self, email: str, contrasena: str | None,
                                 ids_rol: list[int] | None) -> dict:
        """El PATCH: lo que no llega se conserva.

        Y conservar los roles cuesta UNA consulta de mas, porque el
        procedimiento siempre los reemplaza: hay que leer los de ahora para
        volver a mandarlos. No es un rodeo: es la diferencia entre la
        operacion que la base de datos ofrece —reemplazar— y la que la API
        necesita —modificar—, y se paga aqui, no retocando el procedimiento.
        """
        email = self._validar_email(email)
        if ids_rol is None:
            actual = await self._repositorio.consultar(email)
            ids_rol = [rol["idrol"] for rol in (actual.get("roles") or [])]
            if not ids_rol:
                # Un usuario sin roles en la base de datos: no se le puede
                # «conservar» lo que no tiene, y la regla 1 sigue valiendo.
                raise ValueError(
                    "El usuario no tiene roles: mande la lista de roles.")
        # Que no haya llegado NADA lo comprueba el controller, que es el
        # unico que sabe distinguir «mando null» de «no mando el campo»
        # (model_dump(exclude_unset=True)). Aqui ya llego algo.
        return await self._repositorio.actualizar(
            email, contrasena or None, self._validar_roles(ids_rol))

    async def eliminar(self, email: str) -> dict:
        return await self._repositorio.eliminar(self._validar_email(email))
