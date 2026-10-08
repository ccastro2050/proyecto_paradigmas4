"""
Repositorio de ruta para SQL Server — la capa de DATOS.

Unica clase que sabe hablar SQL de este motor y que conoce la cadena de
conexion. Cumple IRepositorioRuta sin heredar de nada (Protocol).

Reglas de la constitucion que se cumplen aqui:
- SQL siempre PARAMETRIZADO (:param) — nunca concatenar valores.
- El SQL queda a la vista (SQLAlchemy solo como ejecutor async, con text()).
- OJO CON EL DIALECTO: aqui el tope va al PRINCIPIO —`SELECT TOP (:n)`—
  y no al final con LIMIT. Es la diferencia que mas se olvida al portar.
- El error del MOTOR se traduce AQUI a una excepcion de NEGOCIO: nadie por
  encima de esta capa conoce `IntegrityError`.

Por que basta con `IntegrityError` en esta tabla: `ruta` no tiene llaves
foraneas: sus unicas restricciones son la primaria y el UNIQUE de la
columna `ruta`. Entonces, si el motor rechaza por integridad, el motivo solo
puede ser uno —esa ruta ya existe—, y eso es un 409. En una tabla CON
foraneas el mismo error significaria dos cosas distintas y habria que mirar
el SQLSTATE para separarlas (como hace el repositorio de factura).
"""

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from excepciones import ConflictoError


class RepositorioRutaSqlServer:
    """Implementacion concreta de IRepositorioRuta contra SQL Server."""

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
        sql = text("SELECT TOP (:limite) id, ruta, descripcion FROM ruta "
                   "ORDER BY id")
        async with self._obtener_engine().connect() as conexion:
            resultado = await conexion.execute(sql, {"limite": limite})
            return [dict(fila._mapping) for fila in resultado]

    async def obtener_por_id(self, id_ruta: int) -> dict | None:
        sql = text("SELECT id, ruta, descripcion FROM ruta WHERE id = :id_ruta")
        async with self._obtener_engine().connect() as conexion:
            resultado = await conexion.execute(sql, {"id_ruta": id_ruta})
            fila = resultado.first()
            return dict(fila._mapping) if fila else None

    async def crear(self, datos: dict) -> bool:
        # El id NO se envia: lo genera la base de datos.
        sql = text("INSERT INTO ruta (ruta, descripcion) "
                   "VALUES (:ruta, :descripcion)")
        # begin() abre una TRANSACCION: si algo falla, nada queda a medias.
        try:
            async with self._obtener_engine().begin() as conexion:
                resultado = await conexion.execute(sql, datos)
                return resultado.rowcount == 1
        except IntegrityError as excepcion:
            # El UNIQUE uq_ruta rechazo el INSERT: la ruta ya existe. No es
            # «usted escribio mal» (400) sino «choca con lo que ya hay» (409).
            raise ConflictoError(
                f"La ruta '{datos['ruta']}' ya existe.") from excepcion

    async def actualizar(self, id_ruta: int, datos: dict) -> int:
        # SET DINAMICO: solo las columnas que llegaron. Los NOMBRES salen de
        # los modelos Pydantic (por eso es seguro interpolarlos); los VALORES
        # van parametrizados.
        asignaciones = ", ".join(f"{columna} = :{columna}" for columna in datos)
        sql = text(f"UPDATE ruta SET {asignaciones} WHERE id = :id_ruta")
        try:
            async with self._obtener_engine().begin() as conexion:
                resultado = await conexion.execute(
                    sql, {**datos, "id_ruta": id_ruta})
                return resultado.rowcount
        except IntegrityError as excepcion:
            # Renombrar una ruta con el nombre de otra: el mismo UNIQUE.
            raise ConflictoError(
                "Ya existe otra ruta con ese nombre.") from excepcion

    async def eliminar(self, id_ruta: int) -> int:
        # Las filas de rutarol que apunten aqui caen con ella: la FK se
        # declaro ON DELETE CASCADE. Borrar una ruta es, por diseno, borrar
        # tambien sus permisos.
        sql = text("DELETE FROM ruta WHERE id = :id_ruta")
        async with self._obtener_engine().begin() as conexion:
            resultado = await conexion.execute(sql, {"id_ruta": id_ruta})
            return resultado.rowcount
