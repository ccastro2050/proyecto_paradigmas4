"""
Servicio de consultas — diez metodos que delegan, y una razon para existir.

Es el servicio mas delgado de la API junto con el de permisos: no valida nada
—una consulta sin parametros no tiene nada que validar— y no transforma nada
—los numeros salen como los calculo el motor—.

ENTONCES POR QUE ESTA, que es la pregunta justa: porque el dia que una de
estas consultas necesite un filtro por fechas, o que el ticket promedio
excluya a los vendedores sin ventas, o que el credito disponible avise cuando
sea negativo, esa regla tiene un sitio donde ir. Si el controller hablara
directo con el repositorio, ese dia habria que mover codigo de capa —y
mientras se mueve, se rompe—.

Las capas no se pagan cuando se escriben: se cobran cuando el sistema cambia.
"""

from repositorios.abstracciones.i_repositorio_consultas import (
    IRepositorioConsultas)


class ServicioConsultas:
    """Implementacion de IServicioConsultas."""

    def __init__(self, repositorio: IRepositorioConsultas):
        self._repositorio = repositorio

    async def ventas_por_producto(self) -> list[dict]:
        return await self._repositorio.ventas_por_producto()

    async def ventas_por_cliente(self) -> list[dict]:
        return await self._repositorio.ventas_por_cliente()

    async def ventas_por_vendedor(self) -> list[dict]:
        return await self._repositorio.ventas_por_vendedor()

    async def ventas_por_empresa(self) -> list[dict]:
        return await self._repositorio.ventas_por_empresa()

    async def ticket_por_vendedor(self) -> list[dict]:
        return await self._repositorio.ticket_por_vendedor()

    async def productos_sin_vender(self) -> list[dict]:
        return await self._repositorio.productos_sin_vender()

    async def anulaciones_por_cliente(self) -> list[dict]:
        return await self._repositorio.anulaciones_por_cliente()

    async def alcance_de_usuarios(self) -> list[dict]:
        return await self._repositorio.alcance_de_usuarios()

    async def interfaces_sin_usuarios(self) -> list[dict]:
        return await self._repositorio.interfaces_sin_usuarios()

    async def credito_contra_consumo(self) -> list[dict]:
        return await self._repositorio.credito_contra_consumo()
