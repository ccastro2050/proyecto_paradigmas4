"""
Repositorio de usuario para PostgreSQL — la capa de DATOS.

AQUI, Y SOLO AQUI, vive el hash. Dos reglas que no se negocian:

1. Se guarda bcrypt con costo 12, jamas texto plano.
2. Ningun SELECT proyecta la columna `contrasena` hacia afuera. El unico que
   la lee es `verificar_contrasena`, y la compara adentro: el hash no sale
   de este archivo.

Un detalle de async que importa de verdad: bcrypt es DELIBERADAMENTE lento
—ahi esta su gracia: unos 250 ms con costo 12—, y es codigo que consume CPU,
no espera de red. Llamarlo directo dentro de una funcion `async` congelaria
el bucle de eventos: mientras una contrasena se hashea, las demas peticiones
quedarian en cola. Por eso va envuelto en `asyncio.to_thread`, que lo manda
a un hilo aparte. Es la diferencia entre una API que aguanta veinte logins
simultaneos y una que los atiende en fila de a uno.

Y una advertencia sobre los datos sembrados: en esta base de datos dos
usuarios quedaron con la contrasena EN TEXTO PLANO ('jefe123', 'cli123').
`bcrypt.checkpw` no sabe leer eso y lanza; por eso la verificacion atrapa la
excepcion y responde False —no coincide— en vez de caerse con un 500. Un
dato malo en la base de datos no puede tumbar la API.
"""

import asyncio

import bcrypt
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine


class RepositorioUsuarioPostgreSQL:
    """Implementacion concreta de IRepositorioUsuario contra PostgreSQL."""

    # El costo del hash: cada punto DUPLICA el tiempo. 12 es el equilibrio
    # habitual entre «molesta al atacante» y «no molesta al usuario».
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
    # El hash, en un hilo aparte (ver el encabezado)
    # ------------------------------------------------------------------
    @classmethod
    async def _hashear(cls, contrasena: str) -> str:
        def trabajo() -> str:
            semilla = bcrypt.gensalt(rounds=cls.COSTO_BCRYPT)
            return bcrypt.hashpw(contrasena.encode("utf-8"), semilla).decode()

        return await asyncio.to_thread(trabajo)

    @staticmethod
    async def _coincide(contrasena: str, hash_guardado: str) -> bool:
        def trabajo() -> bool:
            try:
                return bcrypt.checkpw(contrasena.encode("utf-8"),
                                      hash_guardado.encode("utf-8"))
            except (ValueError, TypeError):
                # El hash guardado esta malformado (texto plano sembrado):
                # no coincide, y la API sigue en pie.
                return False

        return await asyncio.to_thread(trabajo)

    # ------------------------------------------------------------------
    # Los 6 metodos del contrato
    # ------------------------------------------------------------------
    async def obtener_todos(self, limite: int) -> list[dict]:
        # SOLO email: la contrasena no sale ni en hash.
        sql = text("SELECT email FROM usuario ORDER BY email LIMIT :limite")
        async with self._obtener_engine().connect() as conexion:
            resultado = await conexion.execute(sql, {"limite": limite})
            return [dict(fila._mapping) for fila in resultado]

    async def obtener_por_email(self, email: str) -> dict | None:
        sql = text("SELECT email FROM usuario WHERE email = :email")
        async with self._obtener_engine().connect() as conexion:
            resultado = await conexion.execute(sql, {"email": email})
            fila = resultado.first()
            return dict(fila._mapping) if fila else None

    async def crear(self, email: str, contrasena: str) -> bool:
        # El hash se calcula AQUI, justo antes de persistir.
        hash_nuevo = await self._hashear(contrasena)
        sql = text("INSERT INTO usuario (email, contrasena) "
                   "VALUES (:email, :hash_nuevo)")
        async with self._obtener_engine().begin() as conexion:
            resultado = await conexion.execute(
                sql, {"email": email, "hash_nuevo": hash_nuevo})
            return resultado.rowcount == 1

    async def actualizar_contrasena(self, email: str, contrasena: str) -> int:
        hash_nuevo = await self._hashear(contrasena)
        sql = text("UPDATE usuario SET contrasena = :hash_nuevo "
                   "WHERE email = :email")
        async with self._obtener_engine().begin() as conexion:
            resultado = await conexion.execute(
                sql, {"hash_nuevo": hash_nuevo, "email": email})
            return resultado.rowcount

    async def eliminar(self, email: str) -> int:
        # Si el usuario tiene roles, la FK de rol_usuario rechaza el DELETE
        # (no se declaro CASCADE aqui, a diferencia de rutarol): primero se
        # le quitan los roles. El error del motor sube y sale como 500.
        sql = text("DELETE FROM usuario WHERE email = :email")
        async with self._obtener_engine().begin() as conexion:
            resultado = await conexion.execute(sql, {"email": email})
            return resultado.rowcount

    async def verificar_contrasena(self, email: str,
                                   contrasena: str) -> bool | None:
        # El hash SE LEE pero no sale: se compara aqui mismo.
        sql = text("SELECT contrasena FROM usuario WHERE email = :email")
        async with self._obtener_engine().connect() as conexion:
            resultado = await conexion.execute(sql, {"email": email})
            fila = resultado.first()
        if fila is None:
            return None                      # el usuario no existe -> 404
        return await self._coincide(contrasena, fila[0])
