"""
Repositorio de acceso para MariaDB — llama al procedimiento que ya estaba.

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
"""

import json

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine


class RepositorioAccesoMariaDB:
    """Implementacion concreta de IRepositorioAcceso contra MariaDB."""

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
        sql_id = text("SELECT id FROM ruta WHERE ruta = :nombre")
        # MariaDB recoge el OUT en una variable de SESION: las tres
        # sentencias van sobre LA MISMA conexion.
        sql_verificar = text(
            "CALL verificar_acceso_ruta(:email, :id_ruta, @salida)")
        async with self._obtener_engine().begin() as conexion:
            # Paso 1: el nombre a id.
            fila = (await conexion.execute(
                sql_id, {"nombre": nombre_ruta})).first()
            if fila is None:
                return False            # ruta no declarada -> nadie entra
            # Paso 2: el procedimiento, y luego la variable de sesion.
            await conexion.execute(
                sql_verificar, {"email": email, "id_ruta": fila[0]})
            respuesta = (await conexion.execute(text("SELECT @salida"))).first()
        if respuesta is None or respuesta[0] is None:
            return False
        valor = respuesta[0]
        datos = json.loads(valor) if isinstance(valor, str) else valor
        return bool(datos.get("tiene_acceso"))

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
