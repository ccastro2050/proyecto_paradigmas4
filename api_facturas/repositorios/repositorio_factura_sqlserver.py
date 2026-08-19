"""
Repositorio de factura para SQL Server — la API como TRADUCTORA (v4).

El mismo papel que los gemelos PostgreSQL/MariaDB, tercer dialecto:

1. Los SPs devuelven su JSON por un parámetro OUTPUT NVARCHAR(MAX).
   Con ODBC se recoge en un LOTE de tres sentencias: DECLARE la
   variable, EXEC con @p_resultado = @salida OUTPUT, y SELECT @salida
   (SET NOCOUNT ON al frente para que el único resultado sea ese SELECT).
2. Los THROW 50001/50002/50003/50010 de SPs y triggers llegan como
   DBAPIError vía ODBC: se traducen por el PATRÓN del mensaje — los
   mismos textos que en los otros motores ("no existe", "ya está
   anulada"). Tres motores, tres señales, UNA frontera que normaliza.
"""

import json

from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from excepciones import ConflictoError


class RepositorioFacturaSqlServer:
    """Implementación concreta de IRepositorioFactura contra SQL Server."""

    def __init__(self, cadena_conexion: str):
        self._cadena_conexion = cadena_conexion
        self._engine: AsyncEngine | None = None

    def _obtener_engine(self) -> AsyncEngine:
        if self._engine is None:
            self._engine = create_async_engine(self._cadena_conexion)
        return self._engine

    # ------------------------------------------------------------------
    # El ayudante central: el lote DECLARE/EXEC/SELECT y la traducción
    # ------------------------------------------------------------------

    @staticmethod
    def _limpiar_mensaje(texto: str) -> str:
        """Quita el prefijo ODBC ('[42000] [Microsoft][ODBC…]') del mensaje."""
        if "]" in texto:
            texto = texto.rsplit("]", 1)[1]
        return texto.split(" (50")[0].strip().strip("'\"")

    @classmethod
    def _traducir_si_es_negocio(cls, excepcion: DBAPIError) -> None:
        """THROW de los SPs + patrón del mensaje → excepción de negocio."""
        mensaje = cls._limpiar_mensaje(str(excepcion.orig))
        if "no existe" in mensaje:
            raise LookupError(mensaje)          # → 404
        if "anulada" in mensaje:
            raise ConflictoError(mensaje)       # → 409
        # Lo demás (stock insuficiente del trigger, FK, mínimo de
        # renglones) sube tal cual → 500 con el mensaje del motor.

    async def _ejecutar_sp(self, exec_sp: str, parametros: dict) -> dict | list | None:
        # SET NOCOUNT ON: sin él, cada INSERT del SP emite un conteo de
        # filas y el SELECT final dejaría de ser el primer resultado.
        lote = ("SET NOCOUNT ON; DECLARE @salida NVARCHAR(MAX); "
                + exec_sp + " SELECT @salida;")
        try:
            async with self._obtener_engine().begin() as conexion:
                fila = (await conexion.execute(text(lote), parametros)).first()
        except DBAPIError as excepcion:
            self._traducir_si_es_negocio(excepcion)
            raise
        if fila is None or fila[0] is None:
            return None
        valor = fila[0]
        return json.loads(valor) if isinstance(valor, str) else valor

    # ------------------------------------------------------------------
    # Los 4 métodos del contrato (mismos SPs, mismo JSON)
    # ------------------------------------------------------------------

    async def listar(self) -> list[dict]:
        resultado = await self._ejecutar_sp(
            "EXEC sp_listar_facturas_y_productosporfactura "
            "@p_resultado = @salida OUTPUT;", {})
        return resultado or []

    async def consultar(self, numero: int) -> dict:
        resultado = await self._ejecutar_sp(
            "EXEC sp_consultar_factura_y_productosporfactura "
            "@p_numero = :numero, @p_resultado = @salida OUTPUT;",
            {"numero": numero})
        factura = resultado["factura"]
        factura["productos"] = resultado["productos"] or []
        return factura

    async def crear(self, fkidcliente: int, fkidvendedor: int,
                    productos_json: str) -> dict:
        # El detalle viaja como NVARCHAR y el SP lo abre con OPENJSON:
        return await self._ejecutar_sp(
            "EXEC sp_insertar_factura_y_productosporfactura "
            "@p_fkidcliente = :cliente, @p_fkidvendedor = :vendedor, "
            "@p_productos = :productos, @p_resultado = @salida OUTPUT;",
            {"cliente": fkidcliente, "vendedor": fkidvendedor,
             "productos": productos_json})

    async def anular(self, numero: int) -> dict:
        return await self._ejecutar_sp(
            "EXEC sp_anular_factura "
            "@p_numero = :numero, @p_resultado = @salida OUTPUT;",
            {"numero": numero})
