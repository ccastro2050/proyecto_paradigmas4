"""
Contrato del servicio de consultas — las diez, por nombre.

El controller depende de esta interfaz, no de la clase concreta.
"""

from typing import Protocol


class IServicioConsultas(Protocol):
    """Las 10 consultas de la v4, una por metodo."""

    async def ventas_por_producto(self) -> list[dict]:
        ...

    async def ventas_por_cliente(self) -> list[dict]:
        ...

    async def ventas_por_vendedor(self) -> list[dict]:
        ...

    async def ventas_por_empresa(self) -> list[dict]:
        ...

    async def ticket_por_vendedor(self) -> list[dict]:
        ...

    async def productos_sin_vender(self) -> list[dict]:
        ...

    async def anulaciones_por_cliente(self) -> list[dict]:
        ...

    async def alcance_de_usuarios(self) -> list[dict]:
        ...

    async def interfaces_sin_usuarios(self) -> list[dict]:
        ...

    async def credito_contra_consumo(self) -> list[dict]:
        ...
