"""
Servicio de sesion — comprueba las credenciales y arma el token.

Dos decisiones viven aqui, y las dos son del dominio:

1. **UN SOLO ERROR PARA LOS DOS CASOS.** Si el correo no existe y si la
   contrasena esta mal, la respuesta es la misma. Decir «ese correo no
   existe» le confirma a un desconocido CUALES SI existen —y con una lista
   de correos validos, probar contrasenas empieza a valer la pena—.

   Ojo con la aparente contradiccion: `POST /api/usuario/verificar-contrasena`
   SI distingue 404 de 401. Y esta bien que lo haga, porque ese endpoint es
   para un administrador que ya entro, no para la puerta de la calle. **El
   mismo hecho se cuenta distinto segun quien pregunte.**

2. **EL TOKEN LLEVA EL CORREO Y LOS ROLES, Y NADA MAS.** No lleva permisos
   —se consultan al usar— ni datos personales: el contenido de un JWT se lee
   sin ninguna clave (ver `autorizacion/jwt_token.py`).

Y una cosa que este servicio NO hace: no sabe nada de HTTP. Devuelve la
sesion o `None`; convertir ese `None` en 401 es trabajo del controller.
"""

from autorizacion import jwt_token
from repositorios.abstracciones.i_repositorio_rol import IRepositorioRol
from repositorios.abstracciones.i_repositorio_rol_usuario import (
    IRepositorioRolUsuario)
from repositorios.abstracciones.i_repositorio_usuario import (
    IRepositorioUsuario)


class ServicioSesion:
    """Implementacion de IServicioSesion."""

    def __init__(self, usuarios: IRepositorioUsuario,
                 roles_de_usuario: IRepositorioRolUsuario,
                 roles: IRepositorioRol):
        # TRES repositorios, y ninguna clase concreta a la vista: el
        # ensamblador los arma con el motor que diga DB_PROVIDER.
        self._usuarios = usuarios
        self._roles_de_usuario = roles_de_usuario
        self._roles = roles

    async def entrar(self, email: str, contrasena: str) -> dict | None:
        """La sesion, o None si las credenciales no sirven."""
        email = (email or "").strip()
        if not email or not contrasena:
            return None

        # El repositorio compara el HASH, nunca la cadena. Devuelve:
        #   None  -> el correo no existe
        #   False -> existe y la contrasena no coincide
        #   True  -> es
        resultado = await self._usuarios.verificar_contrasena(email, contrasena)

        # LOS DOS CASOS MALOS SE COLAPSAN EN UNO. Quien llama no puede
        # distinguirlos, y eso es lo que se quiere.
        if resultado is not True:
            return None

        return await self._armar(email)

    async def renovar(self, email: str) -> dict | None:
        """Un token nuevo para quien ya trajo uno valido.

        AQUI NO SE PIDE CONTRASENA, y no es un descuido: quien llama ya trajo
        un token valido, y validarlo es exactamente comprobar que en su
        momento dio la contrasena correcta. Pedirla otra vez seria no
        creerle al token que la API misma firmo.

        Lo que SI se vuelve a leer son LOS ROLES: si a alguien le quitaron
        uno, el token nuevo sale sin el. Por eso renovar no es solo correr
        la fecha.
        """
        email = (email or "").strip()
        if not email:
            return None
        return await self._armar(email)

    async def _armar(self, email: str) -> dict:
        roles = await self._nombres_de_roles(email)
        token, expira = jwt_token.firmar(email, roles)
        return {"token": token, "email": email, "roles": roles,
                "expira": expira.isoformat()}

    async def _nombres_de_roles(self, email: str) -> list[str]:
        """Los NOMBRES de los roles, no sus ids.

        El menu de la interfaz le habla a una persona, y «3» no le dice nada
        a nadie. El cruce se hace con los dos repositorios que ya existen en
        vez de pedir un JOIN nuevo: el puente ya sabe traer el nombre.
        """
        asignaciones = await self._roles_de_usuario.obtener_por_usuario(email)
        nombres = [str(fila.get("rol")) for fila in asignaciones
                   if fila.get("rol")]
        if nombres:
            return nombres
        # Si el puente no trajera el nombre —otro motor, otra consulta—, se
        # resuelve con la tabla de roles. Es el camino de respaldo, no el
        # principal.
        todos = {fila["id"]: fila["nombre"]
                 for fila in await self._roles.obtener_todos(1000)}
        return [todos[fila["fkidrol"]] for fila in asignaciones
                if fila.get("fkidrol") in todos]
