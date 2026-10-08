"""
Servicio de permisos — las rutas de quien pregunta.

Es el servicio mas delgado de la API, y esta igual: pasar por la capa de
negocio algo que hoy no tiene reglas cuesta cuatro lineas, y el dia que
tenga una —ocultar rutas de administracion, por ejemplo— ya hay donde
ponerla. Si el controller hablara directo con el repositorio, ese dia
habria que mover codigo de capa.
"""

from repositorios.abstracciones.i_repositorio_acceso import IRepositorioAcceso


class ServicioPermisos:
    """Implementacion de IServicioPermisos."""

    def __init__(self, repositorio: IRepositorioAcceso):
        self._repositorio = repositorio

    async def mis_rutas(self, email: str) -> list[str]:
        email = (email or "").strip()
        if not email:
            raise ValueError("El email no puede estar vacio.")
        return await self._repositorio.rutas_permitidas(email)
