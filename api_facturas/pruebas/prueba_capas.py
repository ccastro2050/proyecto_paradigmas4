"""
prueba_capas.py — Criterio 6 de la v1: el servicio funciona con un
repositorio FALSO en memoria que cumple IRepositorioProducto —
sin PostgreSQL corriendo.

Si esto pasa, las capas quedaron bien cortadas (polimorfismo + inversión de
dependencias): el servicio depende de la INTERFAZ, no del motor.

Ejecutar (desde la carpeta api_facturas):
    python pruebas\\prueba_capas.py
"""

import asyncio
import sys
from pathlib import Path

# El script vive en api_facturas/pruebas/ pero importa desde api_facturas/
# (servicios, repositorios). Se agrega esa carpeta al camino de búsqueda de
# módulos para poder correrlo directo con `python pruebas\prueba_capas.py`:
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from servicios.servicio_persona import ServicioPersona  # noqa: E402
from servicios.servicio_producto import ServicioProducto  # noqa: E402


class RepositorioPersonaFalsoEnMemoria:
    """v2 — el molde una vez más: el falso de PERSONA (mismo contrato que
    el PostgreSQL real, un diccionario por debajo)."""

    def __init__(self):
        self._datos: dict[str, dict] = {}

    async def obtener_todos(self, limite: int) -> list[dict]:
        return [self._datos[c] for c in sorted(self._datos)][:limite]

    async def obtener_por_codigo(self, codigo: str) -> dict | None:
        return self._datos.get(codigo)

    async def crear(self, datos: dict) -> bool:
        self._datos[datos["codigo"]] = dict(datos)
        return True

    async def actualizar(self, codigo: str, datos: dict) -> int:
        if codigo not in self._datos:
            return 0
        self._datos[codigo].update(datos)
        return 1

    async def eliminar(self, codigo: str) -> int:
        if codigo not in self._datos:
            return 0
        del self._datos[codigo]
        return 1


class RepositorioFalsoEnMemoria:
    """El REPOSITORIO FALSO: mismo contrato que el de PostgreSQL, pero
    guarda los productos en un simple diccionario — cero SQL, cero red.

    Note que NO hereda de nada: basta con tener los 5 métodos del Protocol
    (tipado estructural). Como el servicio depende de la interfaz, no nota
    la diferencia.
    """

    def __init__(self):
        # El "almacén": el código como llave y el dict del producto como valor.
        self._datos: dict[str, dict] = {}

    async def obtener_todos(self, limite: int) -> list[dict]:
        # sorted = el ORDER BY codigo; el corte [:limite] = el LIMIT.
        return [self._datos[c] for c in sorted(self._datos)][:limite]

    async def obtener_por_codigo(self, codigo: str) -> dict | None:
        # .get devuelve None si la llave no existe (el contrato).
        return self._datos.get(codigo)

    async def crear(self, datos: dict) -> bool:
        self._datos[datos["codigo"]] = dict(datos)
        return True

    async def actualizar(self, codigo: str, datos: dict) -> int:
        # 0 filas = "no existía" (igual que el rowcount del UPDATE real).
        if codigo not in self._datos:
            return 0
        # Se escriben SOLO los campos que llegaron (como el SET dinámico):
        self._datos[codigo].update(datos)
        return 1

    async def eliminar(self, codigo: str) -> int:
        if codigo not in self._datos:
            return 0
        del self._datos[codigo]
        return 1


def verificar(condicion: bool, descripcion: str) -> None:
    """Mini-verificador: si la condición es falsa, reporta y sale con error.

    (Los scripts que terminan con código 0 pasaron; con != 0, fallaron.)
    """
    if not condicion:
        print(f"FALLÓ: {descripcion}", file=sys.stderr)
        sys.exit(1)


async def main() -> None:
    # La prueba: el MISMO ServicioProducto, con OTRO repositorio (polimorfismo).
    servicio = ServicioProducto(RepositorioFalsoEnMemoria())

    # El ciclo completo contra el repositorio falso:
    await servicio.crear({"codigo": "T1", "nombre": "Test",
                          "stock": 5, "valorunitario": 100.0})
    filas = await servicio.listar(10)
    verificar(filas[0]["codigo"] == "T1", "crear + listar")

    producto = await servicio.obtener("T1")
    verificar(producto["nombre"] == "Test", "obtener por código")

    verificar(await servicio.actualizar("T1", {"stock": 9}) == 1, "actualizar")
    producto = await servicio.obtener("T1")
    verificar(producto["stock"] == 9, "el stock quedó en 9")

    verificar(await servicio.eliminar("T1") == 1, "eliminar")

    # Las excepciones de negocio también funcionan sin BD:
    try:
        await servicio.obtener("NOEXISTE")
        verificar(False, "debió lanzar LookupError (código inexistente)")
    except LookupError:
        pass  # esperado → el controller lo volvería 404

    try:
        await servicio.actualizar("T1", {})
        verificar(False, "debió lanzar ValueError (PATCH sin campos)")
    except ValueError:
        pass  # esperado → 400

    try:
        await servicio.listar(0)
        verificar(False, "debió lanzar ValueError (límite inválido)")
    except ValueError:
        pass  # esperado → 400

    print("CRITERIO 6 OK: el servicio funciona con el repositorio falso, "
          "sin PostgreSQL")

    # ------------------------------------------------------------------
    # v2 — el molde una vez más, ahora PERSONA (criterio 6 de la v2)
    # ------------------------------------------------------------------
    servicio_persona = ServicioPersona(RepositorioPersonaFalsoEnMemoria())

    await servicio_persona.crear({"codigo": "T1", "nombre": "Test",
                                  "email": "t1@test.com", "telefono": "300"})
    lista = await servicio_persona.listar(10)
    verificar(lista[0]["codigo"] == "T1", "persona: crear + listar")
    persona = await servicio_persona.obtener("T1")
    verificar(persona["email"] == "t1@test.com", "persona: obtener")
    verificar(await servicio_persona.actualizar("T1", {"telefono": "301"}) == 1,
              "persona: actualizar")
    verificar(await servicio_persona.eliminar("T1") == 1, "persona: eliminar")

    try:
        await servicio_persona.obtener("NOEXISTE")
        verificar(False, "persona: debió lanzar LookupError")
    except LookupError:
        pass  # esperado → 404

    print("PRUEBA DE CAPAS OK: producto y persona funcionan con "
          "repositorios falsos, sin PostgreSQL")

    # ------------------------------------------------------------------
    # v3 — LA FÁBRICA elige el motor sin abrir conexiones (criterio 5).
    # Construir un repositorio solo guarda la cadena; por eso se puede
    # verificar el patrón con cadenas de mentira.
    # ------------------------------------------------------------------
    import os

    from repositorios.repositorio_factura_mariadb import RepositorioFacturaMariaDB
    from repositorios.repositorio_factura_postgresql import (
        RepositorioFacturaPostgreSQL,
    )
    from repositorios.repositorio_producto_mariadb import (
        RepositorioProductoMariaDB,
    )
    from repositorios.repositorio_producto_postgresql import (
        RepositorioProductoPostgreSQL,
    )
    from servicios import ensamblador

    os.environ.setdefault("DB_POSTGRES", "postgresql+asyncpg://finjo:finjo@nohay/nada")
    os.environ.setdefault("DB_MARIADB", "mysql+aiomysql://finjo:finjo@nohay/nada")

    os.environ["DB_PROVIDER"] = "postgres"
    verificar(isinstance(ensamblador._crear_repositorio("producto"),
                         RepositorioProductoPostgreSQL),
              "fábrica postgres: producto del dialecto correcto")
    verificar(isinstance(ensamblador._crear_repositorio("factura"),
                         RepositorioFacturaPostgreSQL),
              "fábrica postgres: factura del dialecto correcto")

    os.environ["DB_PROVIDER"] = "mariadb"
    verificar(isinstance(ensamblador._crear_repositorio("producto"),
                         RepositorioProductoMariaDB),
              "fábrica mariadb: producto del dialecto correcto")
    verificar(isinstance(ensamblador._crear_repositorio("factura"),
                         RepositorioFacturaMariaDB),
              "fábrica mariadb: factura del dialecto correcto")

    # v4 — el tercer motor en la fábrica:
    from repositorios.repositorio_factura_sqlserver import (
        RepositorioFacturaSqlServer,
    )
    from repositorios.repositorio_producto_sqlserver import (
        RepositorioProductoSqlServer,
    )

    os.environ.setdefault("DB_SQLSERVER", "mssql+aioodbc://finjo:finjo@nohay/nada")
    os.environ["DB_PROVIDER"] = "sqlserver"
    verificar(isinstance(ensamblador._crear_repositorio("producto"),
                         RepositorioProductoSqlServer),
              "fábrica sqlserver: producto del dialecto correcto")
    verificar(isinstance(ensamblador._crear_repositorio("factura"),
                         RepositorioFacturaSqlServer),
              "fábrica sqlserver: factura del dialecto correcto")

    os.environ["DB_PROVIDER"] = "oracle"
    try:
        ensamblador._crear_repositorio("producto")
        verificar(False, "DB_PROVIDER inválido debió fallar con mensaje claro")
    except ValueError as excepcion:
        verificar("inválido" in str(excepcion), "el error del proveedor es claro")
    del os.environ["DB_PROVIDER"]

    print("LA FÁBRICA OK: cada proveedor entrega su dialecto, "
          "sin abrir conexiones")


if __name__ == "__main__":
    asyncio.run(main())
