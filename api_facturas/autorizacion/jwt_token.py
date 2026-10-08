"""
El token: como se firma y como se lee.

UN JWT NO ESTA CIFRADO: ESTA FIRMADO. Cualquiera puede pegar el token en
jwt.io y leer su contenido sin ninguna clave. Lo que la clave garantiza es
otra cosa: que nadie pueda FABRICAR uno ni cambiarle una letra sin que la
firma deje de cuadrar. De ahi la regla:

    en el token va lo que identifica, nunca lo que es secreto.

QUE LLEVA ESTE TOKEN, Y QUE NO
------------------------------
Lleva el correo (`sub`) y los NOMBRES de los roles. No lleva la contrasena
—ni en hash—, ni datos personales, ni los PERMISOS.

Lo de los permisos es la decision importante, y no es un olvido: **el
permiso NO va en el token**. Se consulta en cada peticion con
`verificar_acceso_ruta`. Es mas trabajo —una consulta por operacion— y es lo
que hace que quitarle un permiso a un rol surta efecto DE INMEDIATO, sin
esperar a que el token venza. Si el permiso viajara dentro, la persona
seguiria entrando con el permiso que ya no tiene.

La clave y la duracion salen del entorno (`JWT_CLAVE`, `JWT_MINUTOS`), no
del codigo: una clave escrita en un archivo del repositorio es una clave
publicada.
"""

import os
from datetime import datetime, timedelta, timezone

import jwt

ALGORITMO = "HS256"


def clave() -> str:
    """La clave con la que se firma.

    El valor por omision sirve para el aula y se nota que lo es. En un
    sistema de verdad, sin `JWT_CLAVE` en el entorno, esto deberia negarse
    a arrancar.
    """
    return os.environ.get("JWT_CLAVE", "paradigmas-v4-clave-de-aula")


def minutos() -> int:
    """Cuanto dura un token. Corto no es incomodo: hay renovacion."""
    try:
        return max(1, int(os.environ.get("JWT_MINUTOS", "60")))
    except ValueError:
        return 60


def firmar(email: str, roles: list[str]) -> tuple[str, datetime]:
    """Devuelve (token, cuando expira).

    `exp` es parte del estandar: la propia libreria lo comprueba al leer, y
    por eso no hay que acordarse de mirarlo.
    """
    expira = datetime.now(timezone.utc) + timedelta(minutes=minutos())
    contenido = {
        "sub": email,          # el sujeto: de quien habla el token
        "roles": roles,        # los nombres, para que el menu hable claro
        "exp": expira,         # vencimiento, en UTC
    }
    return jwt.encode(contenido, clave(), algorithm=ALGORITMO), expira


def leer(token: str) -> dict:
    """Comprueba la firma y el vencimiento, y devuelve el contenido.

    Lanza `ValueError` si el token no sirve —vencido, alterado, firmado con
    otra clave—. Quien llama no necesita distinguir el motivo: los tres
    casos son el mismo 401, y decir cual fue le daria pistas a quien esta
    probando.
    """
    try:
        return jwt.decode(token, clave(), algorithms=[ALGORITMO])
    except jwt.PyJWTError as excepcion:
        raise ValueError(f"Token invalido: {excepcion}") from excepcion
