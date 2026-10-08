"""
app.py — El ensamblador del FRONT (Flask + Jinja2).

El front no tiene negocio ni base de datos: rutas que muestran HTML y un
cliente HTTP que habla con la API. Su UNICO estado es la SESION.

LA SESION GUARDA EL TOKEN, y conviene decir donde vive: en la cookie de sesion
de Flask, que va FIRMADA con `CLAVE_SESION` y que el navegador no puede
alterar sin romper la firma.

Lo que NO se hace es guardarlo en `localStorage`: ahi cualquier script de la
pagina lo puede leer. La cookie de sesion de Flask tampoco es perfecta —viaja
al navegador— pero es el mecanismo que el framework ya trae firmado.

Y LA FRASE QUE HAY QUE REPETIR EN CLASE: nada de lo que hace este archivo
protege nada. El `login_requerido` es cortesia —evita que la persona vea un
401 crudo— y el menu filtrado es comodidad. La proteccion esta en la API, que
responde 401 sin token y 403 sin permiso, aunque alguien escriba la direccion
a mano.
"""

import os
from functools import wraps

from flask import Flask, flash, redirect, render_template, request, session, url_for

import cliente_api
from entidades import ENTIDADES
from rutas_entidades import bp as bp_entidades
from rutas_facturas import bp as bp_facturas
# v4 — el tablero: diez consultas multitabla en una pagina, pedidas en
# paralelo (ver rutas_tablero.py).
from rutas_tablero import bp as bp_tablero
# v3 — el usuario CON SUS ROLES: maestro-detalle con casillas, que no cabe
# en el molde de las vistas genericas.
from rutas_usuarios_roles import bp as bp_usuarios_roles

app = Flask(__name__)
# La clave que FIRMA la cookie viaja por variable de entorno, no escrita en el
# codigo: asi se cambia sin recompilar y no queda en el repositorio de nadie.
app.secret_key = os.environ.get("CLAVE_SESION", "clave-solo-para-desarrollo")
app.register_blueprint(bp_entidades)
app.register_blueprint(bp_usuarios_roles)   # la v3: usuario, rol y las puente
app.register_blueprint(bp_tablero)          # la v4: las diez consultas
# v2 — la facturacion maestro-detalle: su propio blueprint, porque no
# es un CRUD. Una factura no se edita: se emite y se anula.
app.register_blueprint(bp_facturas)


# Las tarjetas del inicio que NO salen del registro, porque no son
# un CRUD de campos: la factura se emite y se anula, el usuario con sus
# roles viaja con casillas, y el tablero no tiene tabla.
# El cuarto elemento es EL PERMISO, igual que en `entidades.py`: estas tres
# tambien se esconden si quien entro no lo tiene. Antes salian para todos, y
# era una incoherencia a la vista: el menu ofrecia lo que la API iba a
# rechazar con 403.
TARJETAS_SUELTAS = [
    ("/tablero", "Tablero", 4, "Diez consultas que cruzan cuatro o más tablas", "/home"),
    ("/facturas", "Facturas", 2, "Maestro-detalle: la factura y sus renglones, en un solo envío", "/factura"),
    ("/usuarios-con-roles", "Usuarios y roles", 3, "El usuario y sus roles, con casillas", "/usuario"),
]


@app.context_processor
def menu():
    """EL MENU, ARMADO CON LOS PERMISOS DE QUIEN ESTA IDENTIFICADO.

    Y AQUI VA LA ADVERTENCIA MAS IMPORTANTE DE LA v3:

        ESCONDER UNA ENTRADA DEL MENU NO ES CONTROL DE ACCESO.

    Es la trampa en la que cae casi todo el mundo, porque PARECE que funciona:
    el vendedor entra, no ve «Usuarios», y se va tranquilo.

    Pero este menu es HTML que ya esta en su navegador. Quien escriba la
    direccion a mano llega igual. Lo que lo para es que la API responda 403.

    ENTONCES PARA QUE SIRVE: para no mostrarle a alguien lo que no va a poder
    usar. Es comodidad. La proteccion esta en el servicio.
    """
    # El menu se arma con lo que /api/permisos/mios devolvio al entrar: cada
    # entidad declara el nombre de su ruta y solo sale si esa ruta esta en la
    # lista. Sin sesion no hay permisos y el menu sale vacio —que es lo
    # correcto: todavia no se sabe quien mira—.
    permitidas = session.get("permisos", [])
    visibles = {clave: entidad for clave, entidad in ENTIDADES.items()
                if entidad.get("permiso") in permitidas}
    sueltas = [t for t in TARJETAS_SUELTAS if t[4] in permitidas]
    return {"menu_entidades": visibles, "hay_sesion": "usuario" in session,
            "usuario_actual": session.get("usuario"),
            "roles_actuales": session.get("roles", []),
            "tarjetas_sueltas": sueltas,
            # Para que las plantillas puedan preguntar por un permiso suelto
            # sin repetir la lista: `tiene("/factura")`.
            "tiene": lambda ruta: ruta in permitidas}


def login_requerido(vista):
    """Sin sesion, toda ruta devuelve al login.

    NO es la proteccion —la proteccion es el 401 que responde la API— sino
    cortesia: sin token, la peticion traeria un 401 y la persona veria un error
    en vez de entender que le falta identificarse.
    """

    @wraps(vista)
    def envoltura(*args, **kwargs):
        if "usuario" not in session:
            return redirect(url_for("login"))
        return vista(*args, **kwargs)

    return envoltura


app.jinja_env.globals["login_requerido"] = login_requerido


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        ok, sesion, errores = cliente_api.iniciar_sesion(
            request.form.get("email", "").strip(),
            request.form.get("contrasena", ""),
        )
        if ok:
            session["usuario"] = sesion["email"]
            session["token"] = sesion["token"]
            session["roles"] = sesion.get("roles", [])
            # Los permisos se piden EN SEGUIDA, con el token recien recibido:
            # son los que arman el menu.
            session["permisos"] = cliente_api.mis_permisos(sesion["token"])
            return redirect(url_for("inicio"))
        for e in errores:
            flash(e, "error")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@login_requerido
def inicio():
    return render_template("inicio.html", entidades=ENTIDADES)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PUERTO", "8046")), debug=True)
