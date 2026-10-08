"""
Contrato de las DIEZ consultas de la v4.

Diez metodos con nombre, y ninguno recibe el SQL por parametro. Eso es a
proposito: un `ejecutar(sql)` convertiria este contrato en un tunel para
mandar cualquier cosa a la base de datos, y la inyeccion dejaria de ser un
riesgo teorico. Cada pregunta que la aplicacion sabe responder tiene aqui su
metodo, y lo que no esta aqui no se puede preguntar.

Todas devuelven `list[dict]`: una consulta de reporte no tiene entidad: tiene
columnas. Forzarlas a un modelo de dominio inventaria tipos que no existen en
ninguna tabla.
"""

from typing import Protocol


class IRepositorioConsultas(Protocol):
    """Las 10 consultas multitabla, una por metodo."""

    async def ventas_por_producto(self) -> list[dict]:
        """Que se vende y cuanto deja, por producto."""
        ...

    async def ventas_por_cliente(self) -> list[dict]:
        """Quien compra y cuanto, por cliente."""
        ...

    async def ventas_por_vendedor(self) -> list[dict]:
        """Quien vende y cuanto, por vendedor."""
        ...

    async def ventas_por_empresa(self) -> list[dict]:
        """Cuanto factura cada empresa, sumando a sus clientes."""
        ...

    async def ticket_por_vendedor(self) -> list[dict]:
        """Cuanto vale en promedio una factura de cada vendedor."""
        ...

    async def productos_sin_vender(self) -> list[dict]:
        """Lo que nadie ha comprado nunca —y cuanto capital tiene parado."""
        ...

    async def anulaciones_por_cliente(self) -> list[dict]:
        """Quien anula, cuantas veces y por cuanto."""
        ...

    async def alcance_de_usuarios(self) -> list[dict]:
        """A cuantas interfaces llega cada usuario, por sus roles."""
        ...

    async def interfaces_sin_usuarios(self) -> list[dict]:
        """Rutas a las que NADIE puede entrar: permisos declarados y muertos."""
        ...

    async def credito_contra_consumo(self) -> list[dict]:
        """Cuanto credito tiene cada cliente y cuanto se ha gastado."""
        ...
