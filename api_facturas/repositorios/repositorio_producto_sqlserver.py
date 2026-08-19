"""
Repositorio de producto para SQL Server — la capa de DATOS de la v1.

(v4) El tercer dialecto — y la primera diferencia REAL en los moldes:
T-SQL no tiene LIMIT, tiene TOP (:limite) al principio del SELECT. Todo
lo demás es idéntico a los gemelos PostgreSQL/MariaDB.

Única clase del sistema que sabe hablar SQL y que conoce la cadena de
conexión. Cumple el contrato IRepositorioProducto sin heredar de nada
(Protocol = tipado estructural).

Reglas de la constitución que se cumplen aquí:
- SQL siempre PARAMETRIZADO (:param) — nunca concatenar valores.
- El SQL queda visible (SQLAlchemy solo como ejecutor async, con text()).
"""

from decimal import Decimal

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine


class RepositorioProductoSqlServer:
    """Implementación concreta de IRepositorioProducto contra SQL Server."""

    def __init__(self, cadena_conexion: str):
        # La cadena llega desde afuera (el ensamblador la lee del entorno):
        # este archivo no sabe de variables de entorno ni de configuración.
        self._cadena_conexion = cadena_conexion
        self._engine: AsyncEngine | None = None

    # ------------------------------------------------------------------
    # Ayudantes privados
    # ------------------------------------------------------------------

    def _obtener_engine(self) -> AsyncEngine:
        """Crea el engine async la primera vez y lo reutiliza (perezoso)."""
        if self._engine is None:
            self._engine = create_async_engine(self._cadena_conexion)
        return self._engine

    @staticmethod
    def _serializar(fila: dict) -> dict:
        """Prepara una fila para JSON: NUMERIC llega como Decimal → float."""
        return {
            columna: (float(valor) if isinstance(valor, Decimal) else valor)
            for columna, valor in fila.items()
        }

    # ------------------------------------------------------------------
    # Los 5 métodos del contrato
    # ------------------------------------------------------------------

    async def obtener_todos(self, limite: int) -> list[dict]:
        sql = text(
            "SELECT TOP (:limite) codigo, nombre, stock, valorunitario "
            "FROM producto ORDER BY codigo"
        )
        async with self._obtener_engine().connect() as conexion:
            resultado = await conexion.execute(sql, {"limite": limite})
            return [self._serializar(dict(fila._mapping)) for fila in resultado]

    async def obtener_por_codigo(self, codigo: str) -> dict | None:
        sql = text(
            "SELECT codigo, nombre, stock, valorunitario "
            "FROM producto WHERE codigo = :codigo"
        )
        async with self._obtener_engine().connect() as conexion:
            resultado = await conexion.execute(sql, {"codigo": codigo})
            fila = resultado.first()
            return self._serializar(dict(fila._mapping)) if fila else None

    async def crear(self, datos: dict) -> bool:
        sql = text(
            "INSERT INTO producto (codigo, nombre, stock, valorunitario) "
            "VALUES (:codigo, :nombre, :stock, :valorunitario)"
        )
        # engine.begin() abre una TRANSACCIÓN: si algo falla, nada queda
        # (atomicidad — ver docs/PRINCIPIOS_ACID.md).
        async with self._obtener_engine().begin() as conexion:
            resultado = await conexion.execute(sql, datos)
            return resultado.rowcount == 1

    async def actualizar(self, codigo: str, datos: dict) -> int:
        # SET dinámico SOLO con las columnas que llegaron (PUT manda las 3,
        # PATCH un subconjunto). Los nombres de columna salen de los modelos
        # Pydantic — nunca del cliente — por eso es seguro interpolarlos;
        # los VALORES sí van siempre parametrizados.
        asignaciones = ", ".join(f"{columna} = :{columna}" for columna in datos)
        sql = text(
            f"UPDATE producto SET {asignaciones} WHERE codigo = :codigo_clave"
        )
        async with self._obtener_engine().begin() as conexion:
            resultado = await conexion.execute(
                sql, {**datos, "codigo_clave": codigo}
            )
            return resultado.rowcount

    async def eliminar(self, codigo: str) -> int:
        sql = text("DELETE FROM producto WHERE codigo = :codigo")
        async with self._obtener_engine().begin() as conexion:
            resultado = await conexion.execute(sql, {"codigo": codigo})
            return resultado.rowcount
