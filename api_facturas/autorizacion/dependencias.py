"""
Las dos puertas: 401 y 403.

En .NET esto son dos atributos sobre el controlador —`[Authorize]` y
`[ExigePermiso]`—. En FastAPI son DEPENDENCIAS, y la idea es la misma: se
declaran al lado de la ruta y corren ANTES del cuerpo del endpoint. El
mecanismo cambia con el lenguaje; la decision de diseno, no.

    usuario_actual   ->  401  «no se quien es usted»
    exige_permiso    ->  403  «se quien es, y no puede»

TRES DECISIONES QUE VALE LA PENA LEER DOS VECES
-----------------------------------------------
1. **El permiso se consulta en CADA peticion**, no al entrar. Cuesta una
   consulta por operacion, y es lo que hace que quitar un permiso surta
   efecto sin esperar a que venza el token.

2. **403, no 401.** El token es valido y se sabe perfectamente quien
   pregunta: lo que falta es el permiso. 401 significa «no se quien es
   usted»; 403, «se quien es, y no puede».

3. **Es una dependencia, no una linea dentro del endpoint.** Si fuera una
   linea, el dia que alguien escriba un endpoint nuevo y se le olvide, ese
   endpoint queda abierto —y nadie lo nota, porque funciona—. La dependencia
   va en la firma, a la vista de cualquiera que lea la ruta.
"""

from fastapi import Depends, HTTPException, Request

from autorizacion import jwt_token
from servicios.ensamblador import crear_repositorio_acceso


def _error(estado: int, mensaje: str, detalle: str) -> HTTPException:
    """El MISMO sobre de error que usan los controllers."""
    return HTTPException(
        status_code=estado,
        detail={"estado": estado, "mensaje": mensaje, "detalle": detalle},
        # WWW-Authenticate es lo que la norma pide en un 401: le dice al
        # cliente COMO identificarse, no solo que no lo hizo.
        headers={"WWW-Authenticate": "Bearer"} if estado == 401 else None,
    )


async def usuario_actual(peticion: Request) -> dict:
    """Quien llama, sacado del token. 401 si no hay token o no sirve.

    El correo se lee SIEMPRE del token, nunca del body ni de la URL. Si se
    leyera del body, cualquiera podria escribir el correo de otro y operar
    en su nombre: el token es la unica fuente que la API misma firmo.
    """
    cabecera = peticion.headers.get("Authorization", "")
    if not cabecera.lower().startswith("bearer "):
        raise _error(401, "No hay una sesion valida.",
                     "Falta la cabecera Authorization: Bearer <token>.")
    token = cabecera[7:].strip()
    try:
        contenido = jwt_token.leer(token)
    except ValueError as excepcion:
        # Vencido, alterado o firmado con otra clave: los tres son el mismo
        # 401. Decir cual fue le daria pistas a quien esta probando.
        raise _error(401, "No hay una sesion valida.",
                     str(excepcion)) from excepcion
    email = contenido.get("sub")
    if not email:
        raise _error(401, "No hay una sesion valida.",
                     "El token no dice de quien es.")
    return {"email": email, "roles": contenido.get("roles", [])}


def exige_permiso(nombre_ruta: str):
    """Fabrica la dependencia que exige el permiso de UNA ruta.

    Se usa asi, en la firma del endpoint o del router:

        @router.get("/producto",
                    dependencies=[Depends(exige_permiso("/producto"))])

    Devuelve una funcion porque FastAPI inyecta dependencias sin
    parametros: el nombre de la ruta se captura en el cierre (clausura).
    Es el mismo patron que un decorador con argumentos.
    """

    async def comprobar(quien: dict = Depends(usuario_actual)) -> dict:
        # `usuario_actual` ya respondio 401 si el token no servia; aqui no
        # se llega sin correo. Se comprueba igual: una guardia que SUPONE es
        # una guardia que un dia falla abierta.
        email = quien.get("email")
        if not email:
            raise _error(401, "No hay una sesion valida.",
                         "El token no dice de quien es.")
        acceso = crear_repositorio_acceso()
        if not await acceso.tiene_acceso(email, nombre_ruta):
            raise _error(403, "Su rol no tiene permiso para esta operacion.",
                         f"El usuario {email} no tiene acceso a "
                         f"{nombre_ruta}.")
        return quien

    return comprobar
