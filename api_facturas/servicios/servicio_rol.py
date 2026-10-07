"""
Servicio de rol — las REGLAS, y nada mas.

Lo que este archivo NO sabe, a proposito:
- No sabe que existe HTTP: no devuelve 404, lanza `LookupError`. Traducir
  eso a un codigo es trabajo del controller.
- No sabe contra que motor habla: recibe un IRepositorioRol y le pide
  datos. Si manana es MariaDB, aqui no cambia una linea.
"""

from repositorios.abstracciones.i_repositorio_rol import IRepositorioRol


class ServicioRol:
    """Implementacion de IServicioRol."""

    def __init__(self, repositorio: IRepositorioRol):
        # Inyeccion de dependencias: el repositorio llega armado desde el
        # ensamblador. Este servicio nunca construye uno.
        self._repositorio = repositorio

    @staticmethod
    def _validar_nombre(nombre: str) -> str:
        """El nombre no puede ser espacios en blanco.

        Pydantic ya exigio que viniera y que no fuera vacio; lo que no puede
        ver es que «   » tiene longitud 3 y aun asi no es un nombre.
        """
        limpio = (nombre or "").strip()
        if not limpio:
            raise ValueError("El nombre del rol no puede estar vacio.")
        return limpio

    async def listar(self, limite: int) -> list[dict]:
        return await self._repositorio.obtener_todos(limite)

    async def obtener(self, id_rol: int) -> dict:
        rol = await self._repositorio.obtener_por_id(id_rol)
        if rol is None:
            # LookupError, no HTTPException: aqui no se sabe que es un 404.
            raise LookupError(f"El rol {id_rol} no existe.")
        return rol

    async def crear(self, datos: dict) -> None:
        datos["nombre"] = self._validar_nombre(datos.get("nombre", ""))
        await self._repositorio.crear(datos)

    async def actualizar(self, id_rol: int, datos: dict) -> int:
        if "nombre" in datos and datos["nombre"] is not None:
            datos["nombre"] = self._validar_nombre(datos["nombre"])
        if not datos:
            # Un PATCH vacio no es un error: no hay nada que cambiar.
            return 1
        return await self._repositorio.actualizar(id_rol, datos)

    async def eliminar(self, id_rol: int) -> int:
        return await self._repositorio.eliminar(id_rol)
