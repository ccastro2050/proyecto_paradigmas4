"""
Repositorio de acceso para SQL Server — llama al procedimiento que ya estaba.

`verificar_acceso_ruta` esta en la base de datos desde el primer dia, sin que
nadie lo llamara. Eso es lo que cambia en la v3: no se agrega una tabla, se
empieza a preguntar.

EL PROCEDIMIENTO RECIBE EL ID DE LA RUTA, no su nombre. Asi que hay un paso
antes: traducir `/producto` al id que le corresponde. Se hace aqui y no en la
dependencia de FastAPI, porque es una consulta a la base de datos.

Y hay una decision de seguridad en ese paso: si la ruta NO esta en la tabla,
la respuesta es `False` —nadie entra—. Una ruta que no se declaro no se
concedio. **Fallar cerrado, no abierto**: al contrario, bastaria escribir mal
el nombre de una ruta en el codigo para dejar un endpoint sin proteccion.

EL TIPO DE `tiene_acceso` NO ES EL MISMO EN LOS TRES MOTORES
------------------------------------------------------------
El procedimiento es «el mismo» y su JSON no lo es:

    PostgreSQL   {"tiene_acceso": false}     booleano
    SQL Server   {"tiene_acceso": 0}         numero
    MariaDB      {"tiene_acceso": "0"}       CADENA

Y en Python `bool("0")` es **True**. Un `bool()` a secas aqui concede acceso a
todo el mundo contra MariaDB, sin lanzar nada y sin dejar rastro: **falla
abierto y en silencio**. Por eso la conversion es explicita, esta en los tres
repositorios y lista los valores que acepta — lo que no reconoce es `False`.
"""

import json

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine


class RepositorioAccesoSqlServer:
    """Implementacion concreta de IRepositorioAcceso contra SQL Server."""

    def __init__(self, cadena_conexion: str):
        self._cadena_conexion = cadena_conexion
        self._engine: AsyncEngine | None = None

    def _obtener_engine(self) -> AsyncEngine:
        """Crea el engine async la primera vez y lo reutiliza (perezoso)."""
        if self._engine is None:
            self._engine = create_async_engine(self._cadena_conexion)
        return self._engine

    # ------------------------------------------------------------------
    # Las 2 operaciones del contrato
    # ------------------------------------------------------------------
    async def tiene_acceso(self, email: str, nombre_ruta: str) -> bool:
        sql_id = text("SELECT TOP (1) id FROM ruta WHERE ruta = :nombre")
        # SQL Server devuelve el OUTPUT en un LOTE: DECLARE, EXEC con
        # @p_resultado = @salida OUTPUT, y SELECT @salida.
        sql_verificar = text(
            "SET NOCOUNT ON; DECLARE @salida NVARCHAR(MAX); "
            "EXEC verificar_acceso_ruta @p_email = :email, "
            "@p_fkidruta = :id_ruta, @p_resultado = @salida OUTPUT; "
            "SELECT @salida;")
        async with self._obtener_engine().begin() as conexion:
            # Paso 1: el nombre a id.
            fila = (await conexion.execute(
                sql_id, {"nombre": nombre_ruta})).first()
            if fila is None:
                return False            # ruta no declarada -> nadie entra
            # Paso 2: el lote con el procedimiento.
            respuesta = (await conexion.execute(
                sql_verificar, {"email": email, "id_ruta": fila[0]})).first()
        if respuesta is None or respuesta[0] is None:
            return False
        valor = respuesta[0]
        datos = json.loads(valor) if isinstance(valor, str) else valor
        return self._a_booleano(datos.get("tiene_acceso"))

    @staticmethod
    def _a_booleano(valor) -> bool:
        """Convierte a booleano lo que SQL Server pone en `tiene_acceso`.

        Este motor devuelve un NUMERO: `{"tiene_acceso": 0}`. Con `bool()`
        funcionaria por casualidad —`bool(0)` es `False`—, y esa clase de
        casualidad es la que hace creer que el codigo esta bien hasta que
        se cambia de motor.

        NUNCA `bool(valor)` a secas. En Python `bool("0")` es **True** —una
        cadena no vacia es verdadera—, y escrito asi este metodo concederia
        acceso a todo el mundo. Es el fallo mas peligroso que hay: **falla
        ABIERTO y en silencio**. Sin excepcion, sin registro, y con la
        aplicacion «funcionando».

        Por eso la conversion es explicita y lista los valores que acepta: lo
        que no reconozca es `False` —fallar cerrado, no abierto—.
        """
        if isinstance(valor, bool):
            return valor
        if isinstance(valor, (int, float)):
            return valor == 1
        if isinstance(valor, str):
            return valor.strip().lower() in ("1", "true", "t", "yes")
        return False

    async def rutas_permitidas(self, email: str) -> list[str]:
        # Este SI es un JOIN escrito en Python, y conviene decir por que no
        # contradice la regla de arriba: no decide NADA. Es una lista para
        # dibujar un menu. La DECISION —si una operacion entra o no— la toma
        # `verificar_acceso_ruta`, y solo el.
        sql = text("SELECT DISTINCT r.ruta "
                   "FROM usuario u "
                   "INNER JOIN rol_usuario ru ON u.email = ru.fkemail "
                   "INNER JOIN rutarol rr ON ru.fkidrol = rr.fkidrol "
                   "INNER JOIN ruta r ON r.id = rr.fkidruta "
                   "WHERE u.email = :email "
                   "ORDER BY r.ruta")
        async with self._obtener_engine().connect() as conexion:
            resultado = await conexion.execute(sql, {"email": email})
            return [fila[0] for fila in resultado]
