"""
Contrato del repositorio de rutarol — el puente, que tiene otro patron.

Frente al molde de una entidad (5 metodos) cambian tres cosas:

1. Hay DOS busquedas por lado —por ruta y por rol—, porque las dos
   preguntas son el motivo de la tabla.
2. El `eliminar` exige LAS DOS columnas: la llave primaria es la pareja.
3. Hay dos operaciones que no existen en una entidad normal: `reemplazar`
   —mover una pareja— y `reemplazar_de_rol` —cambiar de un golpe todas las
   rutas de un rol—. Las dos son transaccionales por obligacion, no por
   gusto: a mitad de camino un rol se queda sin poder entrar a nada.
"""

from typing import Protocol


class IRepositorioRutaRol(Protocol):
    """Las 7 operaciones de datos del puente rutarol."""

    async def obtener_todos(self, limite: int) -> list[dict]:
        """Las parejas, con el nombre de la ruta y del rol."""
        ...

    async def obtener_por_ruta(self, fkidruta: int) -> list[dict]:
        """Que roles entran a esta ruta."""
        ...

    async def obtener_por_rol(self, fkidrol: int) -> list[dict]:
        """A que rutas entra este rol."""
        ...

    async def crear(self, fkidruta: int, fkidrol: int) -> bool:
        """Inserta la pareja. Choca si ya existe (llave primaria)."""
        ...

    async def eliminar(self, fkidruta: int, fkidrol: int) -> int:
        """Borra UNA pareja exacta: las dos columnas, no una."""
        ...

    async def reemplazar(self, ruta_vieja: int, rol_viejo: int,
                         ruta_nueva: int, rol_nuevo: int) -> int:
        """MUEVE el permiso: borra la pareja vieja e inserta la nueva.

        En una transaccion, y en ese orden. Devuelve filas afectadas
        (0 = la pareja vieja no existia).
        """
        ...

    async def reemplazar_de_rol(self, fkidrol: int,
                                ids_ruta: list[int]) -> int:
        """Deja al rol EXACTAMENTE con esas rutas. Devuelve cuantas quedaron."""
        ...
