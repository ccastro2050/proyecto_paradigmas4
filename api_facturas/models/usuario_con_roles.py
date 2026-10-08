"""
Modelos Pydantic de usuario-con-roles — el usuario y sus roles, de una vez.

ESTE RECURSO NO ES UNA TABLA. Es una OPERACION que toca dos —`usuario` y
`rol_usuario`— y que tiene que valer como una sola: crear el usuario y
dejarlo sin roles seria crear a alguien que no puede hacer nada, y un paso
intermedio visible por los demas.

Por eso existe aparte de `/api/usuario` y de `/api/rol-usuario`, y por eso lo
resuelven procedimientos almacenados: la transaccion esta donde estan los
datos.

Y por eso `roles` pide `min_length=1`: un usuario sin ningun rol no es un
usuario incompleto, es basura en la tabla. Quien quiera dejar a alguien sin
roles tiene el PUT de `/api/rol-usuario/usuario/{email}` con lista vacia —una
decision administrativa explicita, no un descuido al crear—.
"""

from pydantic import BaseModel, Field

# La misma forma de correo que usan los otros modelos (ver models/usuario.py).
FORMA_EMAIL = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class UsuarioConRolesCrear(BaseModel):
    """POST /api/usuario-con-roles — usuario, contrasena y SUS roles."""

    email: str = Field(max_length=100, pattern=FORMA_EMAIL)
    contrasena: str = Field(min_length=6, max_length=200)
    roles: list[int] = Field(min_length=1)


class UsuarioConRolesReemplazo(BaseModel):
    """PUT /api/usuario-con-roles/{email} — el juego COMPLETO de roles.

    La contrasena es opcional, y eso tiene su razon: la pantalla de casillas
    sirve para cambiar roles, y obligar a reescribir la contrasena para
    guardar un rol haria que alguien la tecleara mal y dejara a otro sin
    poder entrar. Cuando no llega, el procedimiento no la toca.
    """

    roles: list[int] = Field(min_length=1)
    contrasena: str | None = Field(default=None, min_length=6, max_length=200)


class UsuarioConRolesActualizar(BaseModel):
    """PATCH /api/usuario-con-roles/{email} — solo lo que llegue.

    Con dos campos, el PATCH se gana su sitio: permite cambiar la contrasena
    SIN mandar los roles —que es lo que uno quiere cuando solo cambia la
    clave— y al reves. El PUT, en cambio, exige la lista de roles siempre:
    es su semantica.
    """

    roles: list[int] | None = Field(default=None, min_length=1)
    contrasena: str | None = Field(default=None, min_length=6, max_length=200)
