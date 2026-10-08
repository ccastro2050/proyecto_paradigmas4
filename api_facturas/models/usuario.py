"""
Modelos Pydantic de la entidad usuario — la FRONTERA DE ENTRADA.

Esta tabla tiene dos rarezas frente a las demas, y las dos ensenan algo:

1. **La llave primaria es el email**, no un entero autogenerado. Por eso el
   POST SI lleva la llave —el cliente la conoce, no la inventa la base de
   datos— y el id viaja en la URL como texto.

2. **La contrasena entra pero no sale.** Ningun modelo de salida la incluye,
   ni siquiera en hash: una contrasena que viaja en una respuesta ya esta
   comprometida. Los GET de este recurso devuelven solo el email.
"""

from pydantic import BaseModel, Field

# La forma de un correo, sin paquetes de mas: algo, arroba, algo,
# punto, algo. No comprueba que el buzon exista —eso no lo puede saber
# una expresion regular—, solo que lo escrito tenga forma de email.
# Pydantic lo aplica ANTES del servicio: «pepe» es 422, no 400.
#
# Hay un tipo de Pydantic para esto —EmailStr—, y no se usa a
# proposito: exige instalar `email-validator`, que a su vez arrastra
# dnspython. Una dependencia mas para lo que resuelve una linea.
FORMA_EMAIL = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"


class UsuarioCrear(BaseModel):
    """POST /api/usuario — el email y la contrasena en claro.

    `FORMA_EMAIL` valida la forma del correo ANTES de que el servicio exista:
    `pepe` no es un email, y eso es 422, no 400.

    El minimo de 6 caracteres es una regla de forma, y vive aqui. Que la
    contrasena se guarde en hash es una regla de persistencia, y vive en el
    repositorio: este archivo no sabe que existe bcrypt.
    """

    email: str = Field(max_length=100, pattern=FORMA_EMAIL)
    contrasena: str = Field(min_length=6, max_length=200)


class UsuarioReemplazo(BaseModel):
    """PUT /api/usuario/{email} — reemplazo COMPLETO.

    En esta tabla «completo» es una sola columna: la contrasena. El email no
    se reemplaza porque el email ES la llave; cambiarlo seria borrar un
    usuario y crear otro —y arrastrar sus roles—, que es otra operacion.
    """

    contrasena: str = Field(min_length=6, max_length=200)


class UsuarioActualizar(BaseModel):
    """PATCH /api/usuario/{email} — parcial.

    Con una sola columna actualizable, PATCH y PUT hacen lo mismo. Estan los
    dos a proposito: el contrato de la API no cambia porque esta tabla sea
    angosta hoy, y el dia que gane una columna —ultimo ingreso, estado— el
    PATCH ya esta donde debe estar.
    """

    contrasena: str | None = Field(default=None, min_length=6, max_length=200)


class VerificarContrasena(BaseModel):
    """POST /api/usuario/verificar-contrasena — comprobar sin entrar.

    No entrega token: solo responde si la pareja email/contrasena coincide.
    El token lo da `/api/sesion/entrar`, que es otra cosa.
    """

    email: str = Field(max_length=100, pattern=FORMA_EMAIL)
    contrasena: str = Field(min_length=1, max_length=200)
