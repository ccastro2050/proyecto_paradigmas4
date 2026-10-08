"""
Modelos Pydantic de la sesion — entrar y salir.

Lo que NO esta aqui dice tanto como lo que esta: no hay un modelo para
«renovar». Renovar no necesita datos: necesita el token, y el token no viaja
en el body sino en la cabecera. Pedir el correo en el body para renovar
seria dejar que cualquiera renovara la sesion de otro.
"""

from pydantic import BaseModel, Field

# La misma forma de correo que usan los otros modelos (ver models/usuario.py).
FORMA_EMAIL = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class Credenciales(BaseModel):
    """POST /api/sesion/entrar — el unico endpoint abierto de la API.

    La contrasena pide min_length=1 y no 6: aqui no se esta creando nada, se
    esta comprobando. Exigir seis caracteres para INTENTAR entrar le diria a
    quien prueba que las contrasenas cortas no existen en el sistema.
    """

    email: str = Field(max_length=100, pattern=FORMA_EMAIL)
    contrasena: str = Field(min_length=1, max_length=200)
