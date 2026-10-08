"""
Repositorio de usuario-con-roles para SQL Server — la API como TRADUCTORA.

No hay un solo SELECT escrito aqui: cinco llamadas a cinco procedimientos. El
trabajo de este archivo es otro, y son tres cosas:

1. **HASHEAR LA CONTRASENA ANTES DE ENTREGARLA.** El procedimiento la guarda
   tal cual se la den. Si se le pasara en claro, en claro quedaria en la
   tabla —y seria exactamente el error que la v3 viene a corregir—. El hash
   se calcula aqui, con bcrypt costo 12, en un hilo aparte (igual que en el
   repositorio de usuario, y por la misma razon: bcrypt gasta CPU).

2. **TRADUCIR LA LISTA DE ROLES A JSON.** Los procedimientos reciben
   `[{"fkidrol": 1}, {"fkidrol": 3}]` y lo abren con `json_array_elements`.
   Un viaje a la base de datos en vez de uno por rol.

3. **TRADUCIR EL ERROR DEL MOTOR A UNA EXCEPCION DE NEGOCIO.** Los
   `RAISE EXCEPTION 'Usuario % no existe'` llegan como DBAPIError con SQLSTATE
   P0001: aqui (y SOLO aqui) se vuelven LookupError. Nadie por encima conoce
   DBAPIError.
"""

import asyncio
import json

import bcrypt
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from excepciones import ConflictoError


class RepositorioUsuarioConRolesSqlServer:
    """Implementacion de IRepositorioUsuarioConRoles contra SQL Server."""

    COSTO_BCRYPT = 12

    def __init__(self, cadena_conexion: str):
        self._cadena_conexion = cadena_conexion
        self._engine: AsyncEngine | None = None

    def _obtener_engine(self) -> AsyncEngine:
        """Crea el engine async la primera vez y lo reutiliza (perezoso)."""
        if self._engine is None:
            self._engine = create_async_engine(self._cadena_conexion)
        return self._engine

    # ------------------------------------------------------------------
    # Los ayudantes: el hash, el JSON de roles y la traduccion del error
    # ------------------------------------------------------------------
    @classmethod
    async def _hashear(cls, contrasena: str) -> str:
        def trabajo() -> str:
            semilla = bcrypt.gensalt(rounds=cls.COSTO_BCRYPT)
            return bcrypt.hashpw(contrasena.encode("utf-8"), semilla).decode()

        return await asyncio.to_thread(trabajo)

    @staticmethod
    def _roles_json(ids_rol: list[int]) -> str:
        """La lista de enteros, en la forma que esperan los procedimientos."""
        return json.dumps([{"fkidrol": int(i)} for i in ids_rol])

    @staticmethod
    def _traducir_si_es_negocio(excepcion: DBAPIError) -> None:
        """P0001 + patron del mensaje -> excepcion de negocio."""
        mensaje = str(excepcion.orig)
        # SQL Server senala con THROW numerado, y por ODBC el numero no llega
        # limpio: se traduce por el PATRON del mensaje —el mismo texto que
        # escriben los otros dos motores—. Tres motores, tres senales, UNA
        # frontera que las normaliza.
        if "no existe" in mensaje:
            raise LookupError(mensaje)              # -> 404
        if "PRIMARY KEY" in mensaje or "duplicate key" in mensaje.lower():
            raise ConflictoError(mensaje)           # -> 409
        if "FOREIGN KEY" in mensaje or "REFERENCE constraint" in mensaje:
            raise ConflictoError(mensaje)           # -> 409
        # Lo demas sube tal cual -> 500 con el mensaje del motor.

    async def _ejecutar_sp(self, sql_call: str,
                           parametros: dict) -> dict | list | None:
        # SQL Server devuelve el OUTPUT en un LOTE: DECLARE la variable, EXEC
        # con @p_resultado = @salida OUTPUT, y SELECT @salida. SET NOCOUNT ON
        # al frente para que el unico resultado del lote sea ese SELECT.
        lote = text("SET NOCOUNT ON; DECLARE @salida NVARCHAR(MAX); "
                    + sql_call + " SELECT @salida;")
        try:
            async with self._obtener_engine().begin() as conexion:
                fila = (await conexion.execute(lote, parametros)).first()
        except DBAPIError as excepcion:
            self._traducir_si_es_negocio(excepcion)
            raise
        # fila[0] = p_resultado (el INOUT). El dialecto asyncpg ya
        # DESERIALIZA las columnas json; si llegara como texto, se abre aqui.
        if fila is None or fila[0] is None:
            return None
        valor = fila[0]
        return json.loads(valor) if isinstance(valor, str) else valor

    # ------------------------------------------------------------------
    # Las 5 operaciones del contrato
    # ------------------------------------------------------------------
    async def listar(self) -> list[dict]:
        resultado = await self._ejecutar_sp(
            "EXEC listar_usuarios_con_roles @p_resultado = @salida OUTPUT;", {})
        return resultado or []

    async def consultar(self, email: str) -> dict:
        return await self._ejecutar_sp(
            "EXEC consultar_usuario_con_roles @p_email = :email, "
            "@p_resultado = @salida OUTPUT;", {"email": email})

    async def crear(self, email: str, contrasena: str,
                    ids_rol: list[int]) -> dict:
        # El hash, ANTES de entregarselo al procedimiento (ver el encabezado).
        return await self._ejecutar_sp(
            "EXEC crear_usuario_con_roles @p_email = :email, "
            "@p_contrasena = :hash_nuevo, @p_roles_json = :roles, "
            "@p_resultado = @salida OUTPUT;",
            {"email": email,
             "hash_nuevo": await self._hashear(contrasena),
             "roles": self._roles_json(ids_rol)})

    async def actualizar(self, email: str, contrasena: str | None,
                         ids_rol: list[int]) -> dict:
        # Cadena vacia = «no cambie la contrasena». Es la convencion del
        # procedimiento (`IF p_contrasena IS NOT NULL AND p_contrasena != ''`),
        # y el repositorio la respeta en vez de inventar otra.
        hash_nuevo = await self._hashear(contrasena) if contrasena else ""
        return await self._ejecutar_sp(
            "EXEC actualizar_usuario_con_roles @p_email = :email, "
            "@p_contrasena = :hash_nuevo, @p_roles = :roles, "
            "@p_resultado = @salida OUTPUT;",
            {"email": email, "hash_nuevo": hash_nuevo,
             "roles": self._roles_json(ids_rol)})

    async def eliminar(self, email: str) -> dict:
        return await self._ejecutar_sp(
            "EXEC eliminar_usuario_con_roles @p_email = :email, "
            "@p_resultado = @salida OUTPUT;", {"email": email})
