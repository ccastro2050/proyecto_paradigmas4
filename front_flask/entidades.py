"""
entidades.py — El REGISTRO del front: los metadatos de cada entidad.

El molde del front no se copia doce veces: se DESCRIBE cada entidad —endpoint,
llave primaria, campos, llaves foráneas, permiso— y las rutas genéricas hacen
el resto.

POR QUE AQUI SI VALE LO GENERICO Y EN LA API NO, que es la pregunta obvia:

  La API expone un CONTRATO que otros leen y del que dependen. Un
  `/api/{tabla}` deja ese contrato en blanco: Swagger no dice qué recursos hay,
  los permisos no se pueden dar por recurso, y cada cambio toca las doce
  tablas.

  Este archivo no expone nada: es la configuración de UNA aplicación, y el
  contrato que consume —el de la API— sigue siendo específico. Aquí lo
  genérico ahorra doce copias de la misma plantilla sin esconderle nada a
  nadie.

LAS REGLAS DE NEGOCIO SIGUEN TODAS EN LA API. Este registro dice cómo se
DIBUJA cada entidad, no qué se puede hacer con ella.

`url` es la direccion publica del recurso —`/productos`—, la MISMA
que usa el front de Blazor de los otros dos cursos. La clave del
diccionario es el nombre interno; la `url` es lo que se ve.

Cada campo es `(nombre, etiqueta, fk)`, y el tercero es la clave de otra
entidad cuando el campo es una llave foránea: entonces el formulario lo vuelve
un `<select>` cargado desde la API.

EL `permiso` ES EL NOMBRE DE LA RUTA EN LA TABLA `ruta`, tal cual —`/producto`,
`/rol`—. Tiene que coincidir letra por letra con lo que la API exige en su
`exige_permiso(...)` y con lo que devuelve `/api/permisos/mios`; si no
coincide, la entrada del menu simplemente no aparece. Son tres sitios que
hablan del mismo nombre, y la base de datos es la que manda.
"""

# El id del rol Administrador, como lo siembra la base.
ID_ROL_ADMINISTRADOR = 1

# LAS DIEZ ENTIDADES, todas con su endpoint construido en la API. El `desde`
# dice en que version aparecio cada una: 1 las que no tienen foranea, 2 las
# que si, 3 las del control de acceso.
ENTIDADES = {
    "producto": dict(descripcion="Código, nombre, stock y valor unitario", desde=1, url="productos", titulo="Productos", endpoint="/api/producto", pk="codigo",
        permiso="/producto",
        campos=[("codigo", "Código", None), ("nombre", "Nombre", None),
                ("stock", "Stock", None), ("valorunitario", "Valor unitario", None)],
        editable=True),
    "empresa": dict(descripcion="Las empresas a las que puede pertenecer un cliente", desde=1, url="empresas", titulo="Empresas", endpoint="/api/empresa", pk="codigo",
        permiso="/empresa",
        campos=[("codigo", "Código", None), ("nombre", "Nombre", None)],
        editable=True),
    "persona": dict(descripcion="Quiénes son clientes y vendedores", desde=1, url="personas", titulo="Personas", endpoint="/api/persona", pk="codigo",
        permiso="/persona",
        campos=[("codigo", "Código", None), ("nombre", "Nombre", None),
                ("email", "Email", None), ("telefono", "Teléfono", None)],
        editable=True),
    # ── LA v2: las tablas CON clave foránea ──────────────────────────────
    # El tercer elemento de cada campo es la clave de OTRA entidad: cuando
    # está, el formulario lo vuelve un <select> CARGADO DESDE LA API. Esa es
    # la lección de la v2 — la llave foránea se ELIGE, no se escribe.
    "rol": dict(descripcion="Administrador, Vendedor, Cajero, Contador, Cliente", desde=1, url="roles", titulo="Roles", endpoint="/api/rol", pk="id",
        permiso="/rol",
        campos=[("nombre", "Nombre", None)],
        editable=True, pk_generada=True),
    "ruta": dict(descripcion="Las interfaces y acciones protegibles", desde=3, url="rutas", titulo="Rutas", endpoint="/api/ruta", pk="id",
        permiso="/ruta",
        campos=[("ruta", "Ruta", None), ("descripcion", "Descripción", None)],
        editable=True, pk_generada=True),
    # `usuario` es la unica cuya llave primaria NO es generada y ES un texto:
    # el POST la lleva. Y `ocultar_en_lista` no es cosmetica — la API NUNCA
    # devuelve la contrasena, asi que la columna saldria vacia y haria pensar
    # que no hay ninguna puesta.
    "usuario": dict(descripcion="Quiénes pueden entrar al sistema", desde=3, url="usuarios", titulo="Usuarios", endpoint="/api/usuario", pk="email",
        permiso="/usuario",
        campos=[("email", "Email", None), ("contrasena", "Contraseña", None)],
        editable=True, ocultar_en_lista=["contrasena"]),
    "cliente": dict(descripcion="Con su persona y su empresa, elegidas de un desplegable", desde=2, url="clientes", titulo="Clientes", endpoint="/api/cliente", pk="id",
        permiso="/cliente",
        campos=[("credito", "Crédito", None),
                ("fkcodpersona", "Persona", "persona"),
                ("fkcodempresa", "Empresa (opcional)", "empresa")],
        editable=True, pk_generada=True),
    "vendedor": dict(descripcion="Con su carnet y su persona", desde=2, url="vendedores", titulo="Vendedores", endpoint="/api/vendedor", pk="id",
        permiso="/vendedor",
        campos=[("carnet", "Carnet", None), ("direccion", "Dirección", None),
                ("fkcodpersona", "Persona", "persona")],
        editable=True, pk_generada=True),
    # ── LAS DOS PUENTE: `pk=None` y `puente=[...]` ───────────────────────
    # No tienen llave propia: su identidad son LAS DOS columnas, y por eso
    # `editable=False` —no hay ficha que editar, hay parejas que se agregan y
    # se quitan— y el borrado pide las dos.
    #
    # Y junto a «Usuarios y roles» (/usuarios-con-roles) estan la misma
    # relacion vista de dos maneras: aqui pareja por pareja, alla el juego
    # completo con casillas. Verlas al lado es el punto.
    "rol_usuario": dict(descripcion="La tabla puente, pareja a pareja", desde=3, url="rol-usuario", titulo="Roles por usuario", endpoint="/api/rol-usuario",
        pk=None, permiso="/usuario",
        campos=[("fkemail", "Usuario", "usuario"), ("fkidrol", "Rol", "rol")],
        editable=False, puente=["fkemail", "fkidrol"]),
    "rutarol": dict(descripcion="Qué rol entra a qué interfaz", desde=3, url="ruta-rol", titulo="Permisos por rol", endpoint="/api/rutarol",
        pk=None, permiso="/permiso",
        campos=[("fkidruta", "Interfaz o acción", "ruta"), ("fkidrol", "Rol", "rol")],
        editable=False, puente=["fkidruta", "fkidrol"]),
}
