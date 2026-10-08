"""
Servicio de usuario — las REGLAS, y nada mas.

No sabe de bcrypt (eso es del repositorio) ni de HTTP (eso es del
controller). Lo suyo es validar y traducir el resultado de la verificacion a
hechos de negocio.

La decision de diseno que vale la pena ver aqui: el repositorio devuelve
TRES valores —True, False, None— y el servicio los convierte en dos caminos
distintos: `None` es un LookupError (el usuario no existe, 404) y `False` es
un `return False` (existe y la contrasena no coincide, 401). Mezclarlos
—responder «no coincide» a un usuario inexistente— tapa la diferencia; y
separarlos en voz alta, como hace esta API, le dice a un atacante cuales
correos existen. Las dos posturas son defendibles; lo que no se puede es
elegirla por accidente. Aqui se eligio la version didactica: codigos
distintos para hechos distintos, dicho en el contrato.
"""

from excepciones import ConflictoError
from repositorios.abstracciones.i_repositorio_usuario import IRepositorioUsuario


class ServicioUsuario:
    """Implementacion de IServicioUsuario."""

    def __init__(self, repositorio: IRepositorioUsuario):
        self._repositorio = repositorio

    @staticmethod
    def _validar_email(email: str) -> str:
        limpio = (email or "").strip()
        if not limpio:
            raise ValueError("El email no puede estar vacio.")
        return limpio

    async def listar(self, limite: int) -> list[dict]:
        return await self._repositorio.obtener_todos(limite)

    async def obtener(self, email: str) -> dict:
        email = self._validar_email(email)
        usuario = await self._repositorio.obtener_por_email(email)
        if usuario is None:
            raise LookupError(f"El usuario {email} no existe.")
        return usuario

    async def crear(self, email: str, contrasena: str) -> None:
        email = self._validar_email(email)
        # Un email repetido es la llave primaria chocando: eso es 409, y se
        # comprueba ANTES de hashear para no gastar 250 ms en vano.
        if await self._repositorio.obtener_por_email(email) is not None:
            raise ConflictoError(f"El usuario {email} ya existe.")
        await self._repositorio.crear(email, contrasena)

    async def actualizar_contrasena(self, email: str,
                                    contrasena: str | None) -> int:
        email = self._validar_email(email)
        # El PATCH con body {} llega con contrasena None: regla de negocio,
        # porque en esta tabla no hay nada mas que cambiar.
        if not contrasena:
            raise ValueError("No se envio ninguna contrasena para actualizar.")
        return await self._repositorio.actualizar_contrasena(email, contrasena)

    async def eliminar(self, email: str) -> int:
        email = self._validar_email(email)
        return await self._repositorio.eliminar(email)

    async def verificar_contrasena(self, email: str, contrasena: str) -> bool:
        email = self._validar_email(email)
        coincide = await self._repositorio.verificar_contrasena(email, contrasena)
        if coincide is None:
            raise LookupError(f"El usuario {email} no existe.")
        return coincide
