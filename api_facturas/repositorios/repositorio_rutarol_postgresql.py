"""
Repositorio de rutarol para PostgreSQL — la capa de DATOS del puente.

Reglas de la constitucion que se cumplen aqui:
- SQL siempre PARAMETRIZADO (:param) — nunca concatenar valores.
- El SQL queda a la vista (SQLAlchemy solo como ejecutor async, con text()).
- El error del MOTOR se traduce AQUI a una excepcion de NEGOCIO.

Dos cosas que este archivo muestra y las entidades normales no:

**El JOIN del listado.** La tabla guarda numeros —(3, 1)—, y un numero no le
dice nada a quien lee la pantalla. El listado trae los nombres con un JOIN.
Es una decision discutible y conviene saber por que se tomo: el GET plano
seria mas rapido, pero obligaria al front a pedir `ruta` y `rol` aparte y a
cruzarlos el mismo. **El cruce se hace donde estan los datos.**

**Por que hay transacciones aqui y no en producto.** `reemplazar` y
`reemplazar_de_rol` son DOS sentencias que tienen que valer como una. Si el
DELETE pasa y el INSERT falla, el rol no queda como estaba: queda PEOR, sin
permisos. `begin()` garantiza que o pasan las dos o ninguna.

**Y una nota sobre los procedimientos que SI existen.** La base de datos
tiene `crear_rutarol`, `eliminar_rutarol` y `listar_rutarol`. La API no los
usa, a proposito: un INSERT de una fila no gana nada envuelto en un
procedimiento. Un procedimiento se justifica cuando encierra VARIAS
sentencias que deben valer como una —como `sp_insertar_factura_y_productos`—.
Usarlo para una sola sentencia solo reparte el mismo SQL en dos lugares.
"""

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from excepciones import ConflictoError


class RepositorioRutaRolPostgreSQL:
    """Implementacion concreta de IRepositorioRutaRol contra PostgreSQL."""

    def __init__(self, cadena_conexion: str):
        self._cadena_conexion = cadena_conexion
        self._engine: AsyncEngine | None = None

    def _obtener_engine(self) -> AsyncEngine:
        """Crea el engine async la primera vez y lo reutiliza (perezoso)."""
        if self._engine is None:
            self._engine = create_async_engine(self._cadena_conexion)
        return self._engine

    # ------------------------------------------------------------------
    # Los 7 metodos del contrato
    # ------------------------------------------------------------------
    async def obtener_todos(self, limite: int) -> list[dict]:
        sql = text("SELECT rr.fkidruta, rt.ruta, rr.fkidrol, r.nombre AS rol "
                   "FROM rutarol rr "
                   "JOIN ruta rt ON rt.id = rr.fkidruta "
                   "JOIN rol r ON r.id = rr.fkidrol "
                   "ORDER BY rt.ruta, r.nombre LIMIT :limite")
        async with self._obtener_engine().connect() as conexion:
            resultado = await conexion.execute(sql, {"limite": limite})
            return [dict(fila._mapping) for fila in resultado]

    async def obtener_por_ruta(self, fkidruta: int) -> list[dict]:
        sql = text("SELECT rr.fkidruta, rr.fkidrol, r.nombre AS rol "
                   "FROM rutarol rr "
                   "JOIN rol r ON r.id = rr.fkidrol "
                   "WHERE rr.fkidruta = :fkidruta ORDER BY r.nombre")
        async with self._obtener_engine().connect() as conexion:
            resultado = await conexion.execute(sql, {"fkidruta": fkidruta})
            return [dict(fila._mapping) for fila in resultado]

    async def obtener_por_rol(self, fkidrol: int) -> list[dict]:
        sql = text("SELECT rr.fkidrol, rr.fkidruta, rt.ruta "
                   "FROM rutarol rr "
                   "JOIN ruta rt ON rt.id = rr.fkidruta "
                   "WHERE rr.fkidrol = :fkidrol ORDER BY rt.ruta")
        async with self._obtener_engine().connect() as conexion:
            resultado = await conexion.execute(sql, {"fkidrol": fkidrol})
            return [dict(fila._mapping) for fila in resultado]

    async def crear(self, fkidruta: int, fkidrol: int) -> bool:
        sql = text("INSERT INTO rutarol (fkidruta, fkidrol) "
                   "VALUES (:fkidruta, :fkidrol)")
        try:
            async with self._obtener_engine().begin() as conexion:
                resultado = await conexion.execute(
                    sql, {"fkidruta": fkidruta, "fkidrol": fkidrol})
                return resultado.rowcount == 1
        except IntegrityError as excepcion:
            # DOS motivos posibles, y el mensaje los junta a proposito: la
            # pareja ya existe (llave primaria) o uno de los dos ids no
            # existe (foranea). En los dos casos es 409: la peticion esta
            # bien escrita y choca con el estado de la base de datos.
            raise ConflictoError(
                f"No se pudo asignar la ruta {fkidruta} al rol {fkidrol}: "
                "la pareja ya existe, o alguno de los dos no existe."
            ) from excepcion

    async def eliminar(self, fkidruta: int, fkidrol: int) -> int:
        # LAS DOS columnas: borrar por una sola borraria de mas.
        sql = text("DELETE FROM rutarol "
                   "WHERE fkidruta = :fkidruta AND fkidrol = :fkidrol")
        async with self._obtener_engine().begin() as conexion:
            resultado = await conexion.execute(
                sql, {"fkidruta": fkidruta, "fkidrol": fkidrol})
            return resultado.rowcount

    async def reemplazar(self, ruta_vieja: int, rol_viejo: int,
                         ruta_nueva: int, rol_nuevo: int) -> int:
        sql_borrar = text("DELETE FROM rutarol "
                          "WHERE fkidruta = :ruta AND fkidrol = :rol")
        sql_insertar = text("INSERT INTO rutarol (fkidruta, fkidrol) "
                            "VALUES (:ruta, :rol)")
        try:
            # UNA transaccion: si el INSERT falla, el DELETE se deshace.
            async with self._obtener_engine().begin() as conexion:
                borradas = await conexion.execute(
                    sql_borrar, {"ruta": ruta_vieja, "rol": rol_viejo})
                if borradas.rowcount == 0:
                    # La pareja vieja no existia: no hay nada que mover y no
                    # se inserta nada. El servicio lo traduce a 404.
                    return 0
                await conexion.execute(
                    sql_insertar, {"ruta": ruta_nueva, "rol": rol_nuevo})
                return borradas.rowcount
        except IntegrityError as excepcion:
            raise ConflictoError(
                f"No se pudo mover el permiso a ({ruta_nueva}, {rol_nuevo}): "
                "esa pareja ya existe, o alguno de los dos no existe."
            ) from excepcion

    async def reemplazar_de_rol(self, fkidrol: int,
                                ids_ruta: list[int]) -> int:
        sql_borrar = text("DELETE FROM rutarol WHERE fkidrol = :fkidrol")
        sql_insertar = text("INSERT INTO rutarol (fkidruta, fkidrol) "
                            "VALUES (:fkidruta, :fkidrol)")
        try:
            async with self._obtener_engine().begin() as conexion:
                await conexion.execute(sql_borrar, {"fkidrol": fkidrol})
                for id_ruta in ids_ruta:
                    await conexion.execute(
                        sql_insertar,
                        {"fkidruta": id_ruta, "fkidrol": fkidrol})
                return len(ids_ruta)
        except IntegrityError as excepcion:
            # Una lista con un id repetido, o con una ruta que no existe: no
            # queda nada a medias, la transaccion se deshace completa.
            raise ConflictoError(
                f"No se pudieron asignar esas rutas al rol {fkidrol}: hay "
                "una repetida, o alguna ruta no existe."
            ) from excepcion
