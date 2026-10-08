"""
Servicio de rutarol — las REGLAS del puente, y nada mas.

Las reglas propias de esta tabla, dichas en una linea cada una:

- Los dos ids tienen que ser enteros positivos. Pydantic ya lo exige en el
  body; aqui se exige otra vez porque los ids que vienen EN LA URL no pasan
  por el modelo.
- Mover un permiso a la misma pareja no es un error: es una operacion que no
  cambia nada, y se responde como tal.
- Dejar un rol SIN NINGUNA ruta es legal. Parece un error y no lo es: un rol
  recien creado no tiene permisos todavia, y quitarselos todos es una
  decision administrativa valida. Si fuera ilegal, no habria forma de crear
  un rol vacio.
"""

from repositorios.abstracciones.i_repositorio_rutarol import IRepositorioRutaRol


class ServicioRutaRol:
    """Implementacion de IServicioRutaRol."""

    def __init__(self, repositorio: IRepositorioRutaRol):
        self._repositorio = repositorio

    @staticmethod
    def _validar_id(valor: int, nombre: str) -> int:
        if valor is None or valor <= 0:
            raise ValueError(f"El {nombre} debe ser un entero mayor que cero.")
        return valor

    async def listar(self, limite: int) -> list[dict]:
        return await self._repositorio.obtener_todos(limite)

    async def listar_por_ruta(self, fkidruta: int) -> list[dict]:
        self._validar_id(fkidruta, "id de la ruta")
        return await self._repositorio.obtener_por_ruta(fkidruta)

    async def listar_por_rol(self, fkidrol: int) -> list[dict]:
        self._validar_id(fkidrol, "id del rol")
        return await self._repositorio.obtener_por_rol(fkidrol)

    async def crear(self, fkidruta: int, fkidrol: int) -> None:
        self._validar_id(fkidruta, "id de la ruta")
        self._validar_id(fkidrol, "id del rol")
        await self._repositorio.crear(fkidruta, fkidrol)

    async def eliminar(self, fkidruta: int, fkidrol: int) -> int:
        self._validar_id(fkidruta, "id de la ruta")
        self._validar_id(fkidrol, "id del rol")
        return await self._repositorio.eliminar(fkidruta, fkidrol)

    async def reemplazar(self, ruta_vieja: int, rol_viejo: int,
                         ruta_nueva: int, rol_nuevo: int) -> int:
        for valor, nombre in ((ruta_vieja, "id de la ruta actual"),
                              (rol_viejo, "id del rol actual"),
                              (ruta_nueva, "id de la ruta nueva"),
                              (rol_nuevo, "id del rol nuevo")):
            self._validar_id(valor, nombre)
        if (ruta_vieja, rol_viejo) == (ruta_nueva, rol_nuevo):
            # Mover algo a donde ya esta: no hay nada que hacer, y tampoco
            # hay nada que reportar como error.
            return 1
        filas = await self._repositorio.reemplazar(
            ruta_vieja, rol_viejo, ruta_nueva, rol_nuevo)
        if filas == 0:
            raise LookupError(
                f"No existe el permiso ({ruta_vieja}, {rol_viejo}).")
        return filas

    async def reemplazar_de_rol(self, fkidrol: int,
                                ids_ruta: list[int]) -> int:
        self._validar_id(fkidrol, "id del rol")
        for id_ruta in ids_ruta:
            self._validar_id(id_ruta, "id de la ruta")
        # Una lista con repetidos haria chocar la llave primaria a mitad de la
        # transaccion. Se limpia aqui —el orden se conserva— porque pedir dos
        # veces la misma ruta no es un error del administrador: es una
        # casilla marcada dos veces.
        sin_repetidos = list(dict.fromkeys(ids_ruta))
        return await self._repositorio.reemplazar_de_rol(fkidrol, sin_repetidos)
