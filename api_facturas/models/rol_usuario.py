"""
Modelos Pydantic de la tabla puente rol_usuario — usuario <-> rol.

Es la hermana de `rutarol`, y la diferencia vale una clase entera: aqui uno
de los dos lados es TEXTO —el email, que es la llave primaria de usuario— y
el otro es un entero. Una tabla puente no exige que sus dos lados sean
numeros; exige que las dos columnas juntas identifiquen la fila.

Y es la tabla que cierra el circulo del control de acceso:

    usuario --(rol_usuario)--> rol --(rutarol)--> ruta

El procedimiento `verificar_acceso_ruta` recorre justamente ese camino. Sin
estas dos tablas puente, los permisos habria que escribirlos usuario por
usuario y ruta por ruta.
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


class RolUsuarioCrear(BaseModel):
    """POST /api/rol-usuario — la pareja completa; las dos obligatorias."""

    fkemail: str = Field(max_length=100, pattern=FORMA_EMAIL)
    fkidrol: int = Field(gt=0)


class RolUsuarioActualizar(BaseModel):
    """Para el PATCH, que esta APAGADO: llega SOLO el lado que se mueve.

    Se queda escrito aunque su endpoint no este en la API: el contrato de
    la v3 declara cinco endpoints para esta puente y el PATCH no es uno
    —la explicacion esta en el controller—.
    """

    fkemail: str | None = Field(default=None, max_length=100,
                                pattern=FORMA_EMAIL)
    fkidrol: int | None = Field(default=None, gt=0)


class RolesDeUsuario(BaseModel):
    """Para el PUT de la lista completa de roles, que esta APAGADO aqui.

    Y apagarlo no le quita nada al sistema, porque esa operacion SI existe
    en el contrato: `PUT /api/usuario-con-roles/{email}` hace exactamente
    esto, y es la que usa la pantalla de casillas. La misma relacion, dos
    recursos, **un solo sitio donde se escribe**.

    Es la operacion que usa una pantalla de administracion: se marcan los
    roles y se guarda una sola vez. La base de datos ya tiene el
    procedimiento que hace exactamente esto —`actualizar_roles_usuario`—, y
    este recurso lo llama en vez de repetir su logica en Python.
    """

    ids_rol: list[int] = Field(default_factory=list)
