"""
Repositorio de rol_usuario para PostgreSQL — la capa de DATOS del puente.

Reglas de la constitucion que se cumplen aqui:
- SQL siempre PARAMETRIZADO (:param) — nunca concatenar valores.
- El SQL queda a la vista (SQLAlchemy solo como ejecutor async, con text()).
- El error del MOTOR se traduce AQUI a una excepcion de NEGOCIO.

ESTE ARCHIVO HACE LAS DOS COSAS, Y ESO ES LO QUE ENSENA
-------------------------------------------------------
Las cinco operaciones del puente van en SQL escrito aqui. La sexta
—`reemplazar_roles`— llama al procedimiento `actualizar_roles_usuario`, que
ya existe en la base de datos.

Por que no se hacen las dos igual: el procedimiento no solo borra e
inserta; tambien COMPRUEBA que el usuario exista y devuelve los roles que
quedaron, todo dentro de la misma transaccion del motor. Reescribir eso en
Python daria el mismo resultado hoy y dos verdades que mantener manana.

La regla, en una linea: **si la base de datos ya tiene el procedimiento, la
API lo llama; si no lo tiene, el repositorio abre su propia transaccion**
—como hace `rutarol`, donde no hay procedimiento equivalente—.
"""

import json

from sqlalchemy import text
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from excepciones import ConflictoError


class RepositorioRolUsuarioPostgreSQL:
    """Implementacion concreta de IRepositorioRolUsuario contra PostgreSQL."""

    def __init__(self, cadena_conexion: str):
        self._cadena_conexion = cadena_conexion
        self._engine: AsyncEngine | None = None

    def _obtener_engine(self) -> AsyncEngine:
        """Crea el engine async la primera vez y lo reutiliza (perezoso)."""
        if self._engine is None:
            self._engine = create_async_engine(self._cadena_conexion)
        return self._engine

    # ------------------------------------------------------------------
    # Las cinco operaciones en SQL propio
    # ------------------------------------------------------------------
    async def obtener_todos(self, limite: int) -> list[dict]:
        sql = text("SELECT ru.fkemail, ru.fkidrol, r.nombre AS rol "
                   "FROM rol_usuario ru "
                   "JOIN rol r ON r.id = ru.fkidrol "
                   "ORDER BY ru.fkemail, r.nombre LIMIT :limite")
        async with self._obtener_engine().connect() as conexion:
            resultado = await conexion.execute(sql, {"limite": limite})
            return [dict(fila._mapping) for fila in resultado]

    async def obtener_por_usuario(self, fkemail: str) -> list[dict]:
        sql = text("SELECT ru.fkemail, ru.fkidrol, r.nombre AS rol "
                   "FROM rol_usuario ru "
                   "JOIN rol r ON r.id = ru.fkidrol "
                   "WHERE ru.fkemail = :fkemail ORDER BY r.nombre")
        async with self._obtener_engine().connect() as conexion:
            resultado = await conexion.execute(sql, {"fkemail": fkemail})
            return [dict(fila._mapping) for fila in resultado]

    async def obtener_por_rol(self, fkidrol: int) -> list[dict]:
        sql = text("SELECT ru.fkidrol, ru.fkemail "
                   "FROM rol_usuario ru "
                   "WHERE ru.fkidrol = :fkidrol ORDER BY ru.fkemail")
        async with self._obtener_engine().connect() as conexion:
            resultado = await conexion.execute(sql, {"fkidrol": fkidrol})
            return [dict(fila._mapping) for fila in resultado]

    async def crear(self, fkemail: str, fkidrol: int) -> bool:
        sql = text("INSERT INTO rol_usuario (fkemail, fkidrol) "
                   "VALUES (:fkemail, :fkidrol)")
        try:
            async with self._obtener_engine().begin() as conexion:
                resultado = await conexion.execute(
                    sql, {"fkemail": fkemail, "fkidrol": fkidrol})
                return resultado.rowcount == 1
        except IntegrityError as excepcion:
            # La pareja ya existe (llave primaria) o el usuario/rol no existe
            # (foranea): en los dos casos la peticion esta bien escrita y
            # choca con el estado de la base de datos -> 409.
            raise ConflictoError(
                f"No se pudo dar el rol {fkidrol} a {fkemail}: la pareja ya "
                "existe, o el usuario o el rol no existen."
            ) from excepcion

    async def eliminar(self, fkemail: str, fkidrol: int) -> int:
        # LAS DOS columnas: borrar solo por email le quitaria TODOS los roles.
        sql = text("DELETE FROM rol_usuario "
                   "WHERE fkemail = :fkemail AND fkidrol = :fkidrol")
        async with self._obtener_engine().begin() as conexion:
            resultado = await conexion.execute(
                sql, {"fkemail": fkemail, "fkidrol": fkidrol})
            return resultado.rowcount

    async def reemplazar(self, email_viejo: str, rol_viejo: int,
                         email_nuevo: str, rol_nuevo: int) -> int:
        sql_borrar = text("DELETE FROM rol_usuario "
                          "WHERE fkemail = :email AND fkidrol = :rol")
        sql_insertar = text("INSERT INTO rol_usuario (fkemail, fkidrol) "
                            "VALUES (:email, :rol)")
        try:
            # UNA transaccion: si el INSERT falla, el DELETE se deshace.
            async with self._obtener_engine().begin() as conexion:
                borradas = await conexion.execute(
                    sql_borrar, {"email": email_viejo, "rol": rol_viejo})
                if borradas.rowcount == 0:
                    return 0
                await conexion.execute(
                    sql_insertar, {"email": email_nuevo, "rol": rol_nuevo})
                return borradas.rowcount
        except IntegrityError as excepcion:
            raise ConflictoError(
                f"No se pudo mover el rol a ({email_nuevo}, {rol_nuevo}): "
                "esa pareja ya existe, o alguno de los dos no existe."
            ) from excepcion

    # ------------------------------------------------------------------
    # La sexta: la hace el PROCEDIMIENTO (ver el encabezado)
    # ------------------------------------------------------------------
    async def reemplazar_roles(self, fkemail: str,
                               ids_rol: list[int]) -> dict:
        # El procedimiento recibe la lista como JSON —[{"fkidrol": 1}, …]—
        # y la abre con json_array_elements. UN viaje a la base de datos,
        # UNA transaccion, y la comprobacion del usuario adentro.
        roles_json = json.dumps([{"fkidrol": id_rol} for id_rol in ids_rol])
        sql = text("CALL actualizar_roles_usuario("
                   ":email, cast(:roles as json), NULL)")
        try:
            async with self._obtener_engine().begin() as conexion:
                resultado = await conexion.execute(
                    sql, {"email": fkemail, "roles": roles_json})
                fila = resultado.first()
        except DBAPIError as excepcion:
            self._traducir_si_es_negocio(excepcion)
            raise
        # fila[0] = p_resultado, el parametro INOUT del procedimiento.
        if fila is None or fila[0] is None:
            return {"email": fkemail, "roles": []}
        valor = fila[0]
        return json.loads(valor) if isinstance(valor, str) else valor

    @staticmethod
    def _traducir_si_es_negocio(excepcion: DBAPIError) -> None:
        """P0001 (RAISE EXCEPTION) + patron del mensaje -> negocio.

        El procedimiento levanta «Usuario % no existe» cuando el email no
        esta en la tabla: eso es un 404, no un 500 —la base de datos no
        fallo, contesto—. Y si en la lista viene un rol que no existe, el
        motor rechaza por foranea (SQLSTATE 23503): eso es un 409.
        """
        causa = excepcion.orig
        # El asyncpg real puede venir envuelto por el adaptador de SQLAlchemy:
        causa = getattr(causa, "__cause__", None) or causa
        sqlstate = getattr(causa, "sqlstate", None)
        mensaje = getattr(causa, "message", None) or str(causa)
        if sqlstate == "P0001" and "no existe" in mensaje:
            raise LookupError(mensaje)              # -> 404
        if sqlstate == "23503":
            raise ConflictoError(mensaje)           # -> 409
        # Lo demas sube tal cual -> 500 con el mensaje del motor.
