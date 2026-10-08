"""
Repositorio de consultas para PostgreSQL — las DIEZ consultas de la v4.

Aqui NO hay procedimientos almacenados, y es deliberado: una consulta de
reporte cambia cada vez que alguien quiere verla de otra forma, y tenerla en
un procedimiento obliga a tocar la base de datos para cambiar un ORDER BY.
Los procedimientos de este proyecto existen donde hay una REGLA que proteger
—la facturacion, el usuario con sus roles: transacciones—, no donde solo hay
un SELECT.

CADA CONSULTA CRUZA CUATRO O MAS TABLAS. No es un capricho del enunciado: una
consulta de una tabla la responde el CRUD que ya existe. Lo que estas agregan
es la pregunta que NINGUN endpoint anterior podia responder.

EL SQL VA A LA VISTA, como en todo el proyecto: sin ORM. Quien lea esto ve
exactamente lo que la base de datos va a ejecutar.

UN TROPIEZO QUE EN PYTHON NO EXISTE, Y VALE SABER POR QUE
--------------------------------------------------------
El gemelo .NET de este archivo lleva `CAST(COUNT(...) AS INT)` en las diez
consultas, y un comentario largo explicando que sin eso la API responde 500:
en PostgreSQL COUNT() y SUM() sobre enteros devuelven BIGINT —64 bits—, el
modelo de C# pedia `int` y la libreria no podia construir el objeto.

Aqui no hace falta. No porque Python sea mejor, sino porque **no hay modelo
que materializar**: la fila llega como diccionario y el entero de Python no
tiene tamano fijo. El tropiezo era del tipado estatico, no del motor.

Y el precio de esa comodidad se paga en otra parte: si el dia de manana una
consulta devuelve una columna de mas, en C# el compilador —o la libreria— se
queja; aqui pasa en silencio hasta la pantalla. **Los dos lenguajes cobran,
en momentos distintos.** De eso trata el curso.

LO QUE SI HAY QUE VIGILAR EN PYTHON: los NUMERIC de PostgreSQL llegan como
`Decimal`. FastAPI los serializa bien —salen como numero, no como texto—,
pero sumarlos con un `float` en Python lanza TypeError. Si alguna vez hay que
operar con ellos aqui, se convierten explicitamente.

LAS DOS CONSULTAS QUE NO SON IGUALES EN LOS TRES MOTORES, y se descubrieron
ejecutandolas, no leyendo la documentacion:

  alcance_de_usuarios    PostgreSQL acepta STRING_AGG(DISTINCT x, ', ').
                         T-SQL responde «Incorrect syntax near ','»: su
                         STRING_AGG no admite DISTINCT. MariaDB no tiene
                         STRING_AGG: usa GROUP_CONCAT.

  ticket_por_vendedor    En T-SQL, COUNT() devuelve int y dividir un decimal
                         entre un int TRUNCA —el promedio sale sin
                         centavos—. Hace falta el CAST explicito. PostgreSQL
                         promueve el tipo solo.

Las otras ocho son identicas palabra por palabra. Y eso tambien es un dato:
el SQL estandar llega mas lejos de lo que se suele creer — lo que cambia son
las funciones de agregacion y las reglas de tipos.
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine


class RepositorioConsultasPostgreSQL:
    """Implementacion concreta de IRepositorioConsultas contra PostgreSQL."""

    def __init__(self, cadena_conexion: str):
        self._cadena_conexion = cadena_conexion
        self._engine: AsyncEngine | None = None

    def _obtener_engine(self) -> AsyncEngine:
        """Crea el engine async la primera vez y lo reutiliza (perezoso)."""
        if self._engine is None:
            self._engine = create_async_engine(self._cadena_conexion)
        return self._engine

    async def _filas(self, sql: str) -> list[dict]:
        """Ejecuta y devuelve filas como diccionarios.

        `connect()` y no `begin()`: estas diez SOLO LEEN. Abrir una
        transaccion de escritura para un SELECT no es un error, pero dice una
        mentira sobre lo que el codigo hace.
        """
        async with self._obtener_engine().connect() as conexion:
            resultado = await conexion.execute(text(sql))
            return [dict(fila._mapping) for fila in resultado]

    # ------------------------------------------------------------------
    # 1. Ventas por producto — producto, renglon, factura, cliente
    # ------------------------------------------------------------------
    async def ventas_por_producto(self) -> list[dict]:
        return await self._filas("""
            SELECT p.codigo, p.nombre,
                   SUM(pf.cantidad) AS unidades,
                   SUM(pf.subtotal) AS ingreso,
                   COUNT(DISTINCT f.numero) AS facturas,
                   COUNT(DISTINCT c.id) AS clientes
            FROM producto p
            INNER JOIN productosporfactura pf ON pf.fkcodproducto = p.codigo
            INNER JOIN factura f ON f.numero = pf.fknumfactura
            INNER JOIN cliente c ON c.id = f.fkidcliente
            WHERE f.estado = 'activa'
            GROUP BY p.codigo, p.nombre
            ORDER BY SUM(pf.subtotal) DESC
        """)

    # ------------------------------------------------------------------
    # 2. Ventas por cliente — cliente, persona, factura, renglon
    # ------------------------------------------------------------------
    async def ventas_por_cliente(self) -> list[dict]:
        return await self._filas("""
            SELECT c.id, pe.nombre AS cliente, pe.email,
                   COUNT(DISTINCT f.numero) AS facturas,
                   SUM(pf.subtotal) AS comprado,
                   SUM(pf.cantidad) AS unidades
            FROM cliente c
            INNER JOIN persona pe ON pe.codigo = c.fkcodpersona
            INNER JOIN factura f ON f.fkidcliente = c.id
            INNER JOIN productosporfactura pf ON pf.fknumfactura = f.numero
            WHERE f.estado = 'activa'
            GROUP BY c.id, pe.nombre, pe.email
            ORDER BY SUM(pf.subtotal) DESC
        """)

    # ------------------------------------------------------------------
    # 3. Ventas por vendedor — vendedor, persona, factura, renglon
    # ------------------------------------------------------------------
    async def ventas_por_vendedor(self) -> list[dict]:
        return await self._filas("""
            SELECT v.id, pe.nombre AS vendedor, v.carnet,
                   COUNT(DISTINCT f.numero) AS facturas,
                   SUM(pf.subtotal) AS vendido
            FROM vendedor v
            INNER JOIN persona pe ON pe.codigo = v.fkcodpersona
            INNER JOIN factura f ON f.fkidvendedor = v.id
            INNER JOIN productosporfactura pf ON pf.fknumfactura = f.numero
            WHERE f.estado = 'activa'
            GROUP BY v.id, pe.nombre, v.carnet
            ORDER BY SUM(pf.subtotal) DESC
        """)

    # ------------------------------------------------------------------
    # 4. Ventas por empresa — empresa, cliente, factura, renglon
    # ------------------------------------------------------------------
    async def ventas_por_empresa(self) -> list[dict]:
        return await self._filas("""
            SELECT e.codigo, e.nombre AS empresa,
                   COUNT(DISTINCT c.id) AS clientes,
                   COUNT(DISTINCT f.numero) AS facturas,
                   SUM(pf.subtotal) AS facturado
            FROM empresa e
            INNER JOIN cliente c ON c.fkcodempresa = e.codigo
            INNER JOIN factura f ON f.fkidcliente = c.id
            INNER JOIN productosporfactura pf ON pf.fknumfactura = f.numero
            WHERE f.estado = 'activa'
            GROUP BY e.codigo, e.nombre
            ORDER BY SUM(pf.subtotal) DESC
        """)

    # ------------------------------------------------------------------
    # 5. Ticket promedio por vendedor — OJO: no es igual en los tres
    # ------------------------------------------------------------------
    async def ticket_por_vendedor(self) -> list[dict]:
        # NULLIF evita la division por cero cuando un vendedor no tiene
        # facturas activas: sin el, el motor aborta la consulta entera.
        return await self._filas("""
            SELECT pe.nombre AS vendedor,
                   COUNT(DISTINCT f.numero) AS facturas,
                   SUM(pf.subtotal) AS total,
                   ROUND(SUM(pf.subtotal)
                         / NULLIF(COUNT(DISTINCT f.numero), 0), 2)
                       AS ticket_promedio
            FROM vendedor v
            INNER JOIN persona pe ON pe.codigo = v.fkcodpersona
            INNER JOIN factura f ON f.fkidvendedor = v.id
            INNER JOIN productosporfactura pf ON pf.fknumfactura = f.numero
            WHERE f.estado = 'activa'
            GROUP BY pe.nombre
            ORDER BY 4 DESC
        """)

    # ------------------------------------------------------------------
    # 6. Productos que nunca se han vendido — y aqui el JOIN es IZQUIERDO
    # ------------------------------------------------------------------
    async def productos_sin_vender(self) -> list[dict]:
        # LEFT JOIN + HAVING COUNT = 0: la unica forma de preguntar por lo que
        # NO esta. Con INNER JOIN estos productos no apareceran nunca, porque
        # no tienen fila en el detalle — y la consulta devolveria vacio
        # diciendo «todo se vende».
        return await self._filas("""
            SELECT p.codigo, p.nombre, p.stock, p.valorunitario
            FROM producto p
            LEFT JOIN productosporfactura pf ON pf.fkcodproducto = p.codigo
            LEFT JOIN factura f
                   ON f.numero = pf.fknumfactura AND f.estado = 'activa'
            LEFT JOIN cliente c ON c.id = f.fkidcliente
            GROUP BY p.codigo, p.nombre, p.stock, p.valorunitario
            HAVING COUNT(c.id) = 0
            ORDER BY p.valorunitario DESC
        """)

    # ------------------------------------------------------------------
    # 7. Anulaciones por cliente — la cara B de la consulta 2
    # ------------------------------------------------------------------
    async def anulaciones_por_cliente(self) -> list[dict]:
        # La MISMA consulta de ventas por cliente con `estado = 'anulada'`.
        # Y eso ensena algo del diseno de la tabla: la factura no se borra al
        # anularse, cambia de estado. Si se borrara, esta consulta no se
        # podria escribir.
        return await self._filas("""
            SELECT pe.nombre AS cliente,
                   COUNT(DISTINCT f.numero) AS anuladas,
                   SUM(pf.subtotal) AS valor_anulado
            FROM factura f
            INNER JOIN cliente c ON c.id = f.fkidcliente
            INNER JOIN persona pe ON pe.codigo = c.fkcodpersona
            INNER JOIN productosporfactura pf ON pf.fknumfactura = f.numero
            WHERE f.estado = 'anulada'
            GROUP BY pe.nombre
            ORDER BY SUM(pf.subtotal) DESC
        """)

    # ------------------------------------------------------------------
    # 8. Alcance de cada usuario — OJO: no es igual en los tres motores
    # ------------------------------------------------------------------
    async def alcance_de_usuarios(self) -> list[dict]:
        # CINCO tablas: usuario, rol_usuario, rol, rutarol, ruta. Es el camino
        # completo del control de acceso, visto como reporte.
        return await self._filas("""
            SELECT u.email,
                   COUNT(DISTINCT r.id) AS roles,
                   COUNT(DISTINCT rt.id) AS interfaces,
                   STRING_AGG(DISTINCT r.nombre, ', ') AS sus_roles
            FROM usuario u
            INNER JOIN rol_usuario ru ON ru.fkemail = u.email
            INNER JOIN rol r ON r.id = ru.fkidrol
            INNER JOIN rutarol rr ON rr.fkidrol = r.id
            INNER JOIN ruta rt ON rt.id = rr.fkidruta
            GROUP BY u.email
            ORDER BY COUNT(DISTINCT rt.id) DESC, u.email
        """)

    # ------------------------------------------------------------------
    # 9. Interfaces a las que no llega nadie
    # ------------------------------------------------------------------
    async def interfaces_sin_usuarios(self) -> list[dict]:
        # Un permiso declarado al que ningun usuario alcanza: ni esta mal ni
        # esta bien, pero conviene saber que existe —suele ser una ruta que
        # alguien creo y nadie conecto—.
        return await self._filas("""
            SELECT rt.id, rt.ruta, rt.descripcion,
                   COUNT(DISTINCT r.id) AS roles_con_acceso,
                   COUNT(DISTINCT ru.fkemail) AS usuarios_con_acceso
            FROM ruta rt
            LEFT JOIN rutarol rr ON rr.fkidruta = rt.id
            LEFT JOIN rol r ON r.id = rr.fkidrol
            LEFT JOIN rol_usuario ru ON ru.fkidrol = r.id
            GROUP BY rt.id, rt.ruta, rt.descripcion
            HAVING COUNT(DISTINCT ru.fkemail) = 0
            ORDER BY rt.ruta
        """)

    # ------------------------------------------------------------------
    # 10. Credito contra consumo
    # ------------------------------------------------------------------
    async def credito_contra_consumo(self) -> list[dict]:
        # El LEFT JOIN a empresa es el que importa: `fkcodempresa` es NULL
        # para el cliente que compra a nombre propio, y con INNER JOIN esos
        # clientes desaparecerian del reporte sin que nadie lo notara.
        return await self._filas("""
            SELECT pe.nombre AS cliente,
                   COALESCE(e.nombre, '(sin empresa)') AS empresa,
                   c.credito,
                   COALESCE(SUM(f.total), 0) AS consumido,
                   c.credito - COALESCE(SUM(f.total), 0) AS disponible
            FROM cliente c
            INNER JOIN persona pe ON pe.codigo = c.fkcodpersona
            LEFT JOIN empresa e ON e.codigo = c.fkcodempresa
            LEFT JOIN factura f
                   ON f.fkidcliente = c.id AND f.estado = 'activa'
            GROUP BY pe.nombre, e.nombre, c.credito
            ORDER BY 5
        """)
