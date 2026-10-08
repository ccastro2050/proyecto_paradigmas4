"""
Servicio de ruta — las REGLAS, y nada mas.

Lo que este archivo NO sabe, a proposito:
- No sabe que existe HTTP: no devuelve 404, lanza `LookupError`.
- No sabe contra que motor habla: recibe un IRepositorioRuta.

La regla propia de esta entidad: una ruta se escribe `/algo`. La base de
datos no lo exige —para ella es un VARCHAR cualquiera—, y por eso lo exige
el negocio: sin la barra, `verificar_acceso_ruta` nunca encontraria la ruta
que el front pide.
"""

from repositorios.abstracciones.i_repositorio_ruta import IRepositorioRuta


class ServicioRuta:
    """Implementacion de IServicioRuta."""

    def __init__(self, repositorio: IRepositorioRuta):
        # Inyeccion de dependencias: el repositorio llega armado desde el
        # ensamblador. Este servicio nunca construye uno.
        self._repositorio = repositorio

    @staticmethod
    def _validar_ruta(ruta: str) -> str:
        """La ruta no puede ser espacios, y empieza por barra."""
        limpia = (ruta or "").strip()
        if not limpia:
            raise ValueError("La ruta no puede estar vacia.")
        if not limpia.startswith("/"):
            raise ValueError(
                f"La ruta debe empezar por '/': llego '{limpia}'.")
        return limpia

    @staticmethod
    def _validar_descripcion(descripcion: str) -> str:
        limpia = (descripcion or "").strip()
        if not limpia:
            raise ValueError("La descripcion no puede estar vacia.")
        return limpia

    async def listar(self, limite: int) -> list[dict]:
        return await self._repositorio.obtener_todos(limite)

    async def obtener(self, id_ruta: int) -> dict:
        ruta = await self._repositorio.obtener_por_id(id_ruta)
        if ruta is None:
            # LookupError, no HTTPException: aqui no se sabe que es un 404.
            raise LookupError(f"La ruta {id_ruta} no existe.")
        return ruta

    async def crear(self, datos: dict) -> None:
        datos["ruta"] = self._validar_ruta(datos.get("ruta", ""))
        datos["descripcion"] = self._validar_descripcion(
            datos.get("descripcion", ""))
        await self._repositorio.crear(datos)

    async def actualizar(self, id_ruta: int, datos: dict) -> int:
        if datos.get("ruta") is not None:
            datos["ruta"] = self._validar_ruta(datos["ruta"])
        if datos.get("descripcion") is not None:
            datos["descripcion"] = self._validar_descripcion(
                datos["descripcion"])
        if not datos:
            # Un PATCH vacio no es un error: no hay nada que cambiar.
            return 1
        return await self._repositorio.actualizar(id_ruta, datos)

    async def eliminar(self, id_ruta: int) -> int:
        return await self._repositorio.eliminar(id_ruta)
