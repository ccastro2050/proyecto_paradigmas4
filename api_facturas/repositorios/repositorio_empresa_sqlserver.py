"""
Repositorio de empresa para SQL Server — la capa de DATOS (v2).

(v4) El tercer dialecto — y la primera diferencia REAL en los moldes:
T-SQL no tiene LIMIT, tiene TOP (:limite) al principio del SELECT. Todo
lo demás es idéntico a los gemelos PostgreSQL/MariaDB.

CALCADO del repositorio de producto de la v1: SQLAlchemy async como
ejecutor, SQL visible y parametrizado con text().
"""

from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine


class RepositorioEmpresaSqlServer:
    """Implementación concreta de IRepositorioEmpresa contra SQL Server."""

    def __init__(self, cadena_conexion: str):
        self._cadena_conexion = cadena_conexion
        self._engine: AsyncEngine | None = None

    def _obtener_engine(self) -> AsyncEngine:
        if self._engine is None:
            self._engine = create_async_engine(self._cadena_conexion)
        return self._engine

    @staticmethod
    def _serializar(fila: dict) -> dict:
        return {
            columna: (float(valor) if isinstance(valor, Decimal) else valor)
            for columna, valor in fila.items()
        }

    async def obtener_todos(self, limite: int) -> list[dict]:
        sql = text(
            "SELECT TOP (:limite) codigo, nombre "
            "FROM empresa ORDER BY codigo"
        )
        async with self._obtener_engine().connect() as conexion:
            resultado = await conexion.execute(sql, {"limite": limite})
            return [self._serializar(dict(fila._mapping)) for fila in resultado]

    async def obtener_por_codigo(self, codigo: str) -> dict | None:
        sql = text(
            "SELECT codigo, nombre "
            "FROM empresa WHERE codigo = :codigo"
        )
        async with self._obtener_engine().connect() as conexion:
            resultado = await conexion.execute(sql, {"codigo": codigo})
            fila = resultado.first()
            return self._serializar(dict(fila._mapping)) if fila else None

    async def crear(self, datos: dict) -> bool:
        sql = text(
            "INSERT INTO empresa (codigo, nombre) VALUES (:codigo, :nombre)"
        )
        async with self._obtener_engine().begin() as conexion:
            resultado = await conexion.execute(sql, datos)
            return resultado.rowcount == 1

    async def actualizar(self, codigo: str, datos: dict) -> int:
        asignaciones = ", ".join(f"{columna} = :{columna}" for columna in datos)
        sql = text(
            f"UPDATE empresa SET {asignaciones} WHERE codigo = :pk_clave"
        )
        async with self._obtener_engine().begin() as conexion:
            resultado = await conexion.execute(
                sql, {**datos, "pk_clave": codigo}
            )
            return resultado.rowcount

    async def eliminar(self, codigo: str) -> int:
        # Si la empresa tiene clientes, la FK rechaza → 500.
        sql = text("DELETE FROM empresa WHERE codigo = :codigo")
        async with self._obtener_engine().begin() as conexion:
            resultado = await conexion.execute(sql, {"codigo": codigo})
            return resultado.rowcount
