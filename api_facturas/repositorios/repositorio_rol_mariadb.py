"""
Repositorio de rol para MariaDB — la capa de DATOS.

Unica clase que sabe hablar SQL de este motor y que conoce la cadena de
conexion. Cumple IRepositorioRol sin heredar de nada (Protocol).

Reglas de la constitucion que se cumplen aqui:
- SQL siempre PARAMETRIZADO (:param) — nunca concatenar valores.
- El SQL queda a la vista (SQLAlchemy solo como ejecutor async, con text()).

- Mismo SQL que PostgreSQL aqui: LIMIT va al final en los dos.
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine


class RepositorioRolMariaDB:
    """Implementacion concreta de IRepositorioRol contra MariaDB."""

    def __init__(self, cadena_conexion: str):
        # La cadena llega desde afuera (el ensamblador la lee del entorno):
        # este archivo no sabe de variables de entorno ni de configuracion.
        self._cadena_conexion = cadena_conexion
        self._engine: AsyncEngine | None = None

    def _obtener_engine(self) -> AsyncEngine:
        """Crea el engine async la primera vez y lo reutiliza (perezoso)."""
        if self._engine is None:
            self._engine = create_async_engine(self._cadena_conexion)
        return self._engine

    # ------------------------------------------------------------------
    # Los 5 metodos del contrato
    # ------------------------------------------------------------------
    async def obtener_todos(self, limite: int) -> list[dict]:
        sql = text("SELECT id, nombre FROM rol ORDER BY id LIMIT :limite")
        async with self._obtener_engine().connect() as conexion:
            resultado = await conexion.execute(sql, {"limite": limite})
            return [dict(fila._mapping) for fila in resultado]

    async def obtener_por_id(self, id_rol: int) -> dict | None:
        sql = text("SELECT id, nombre FROM rol WHERE id = :id_rol")
        async with self._obtener_engine().connect() as conexion:
            resultado = await conexion.execute(sql, {"id_rol": id_rol})
            fila = resultado.first()
            return dict(fila._mapping) if fila else None

    async def crear(self, datos: dict) -> bool:
        # El id NO se envia: lo genera la base de datos.
        sql = text("INSERT INTO rol (nombre) VALUES (:nombre)")
        # begin() abre una TRANSACCION: si algo falla, nada queda a medias.
        async with self._obtener_engine().begin() as conexion:
            resultado = await conexion.execute(sql, datos)
            return resultado.rowcount == 1

    async def actualizar(self, id_rol: int, datos: dict) -> int:
        # SET DINAMICO: solo las columnas que llegaron. Los NOMBRES salen de
        # los modelos Pydantic (por eso es seguro interpolarlos); los VALORES
        # van parametrizados.
        asignaciones = ", ".join(f"{columna} = :{columna}" for columna in datos)
        sql = text(f"UPDATE rol SET {asignaciones} WHERE id = :id_rol")
        async with self._obtener_engine().begin() as conexion:
            resultado = await conexion.execute(sql, {**datos, "id_rol": id_rol})
            return resultado.rowcount

    async def eliminar(self, id_rol: int) -> int:
        sql = text("DELETE FROM rol WHERE id = :id_rol")
        async with self._obtener_engine().begin() as conexion:
            resultado = await conexion.execute(sql, {"id_rol": id_rol})
            return resultado.rowcount
