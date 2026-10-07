"""
Modelos Pydantic de la entidad rol — la FRONTERA DE ENTRADA de la API.

`rol` tiene CLAVE GENERADA por la base de datos (`id`), y eso cambia los
modelos respecto a `producto`:

- El POST **no lleva id**: lo pone el motor. Mandarlo seria pedirle al
  cliente que adivine un numero que todavia no existe.
- El id viaja en la URL para PUT, PATCH y DELETE.

Un modelo por semantica HTTP (ver 6_contracts.md).
"""

from pydantic import BaseModel, Field


class Rol(BaseModel):
    """POST /api/rol — solo el nombre: el id lo genera la base de datos."""

    nombre: str = Field(min_length=1, max_length=50)


class RolReemplazo(BaseModel):
    """PUT /api/rol/{id} — reemplazo COMPLETO.

    Omitir el nombre es 422, no «dejarlo como estaba»: esa es la semantica
    de PUT.
    """

    nombre: str = Field(min_length=1, max_length=50)


class RolActualizar(BaseModel):
    """PATCH /api/rol/{id} — parcial: solo se modifica lo que llego."""

    nombre: str | None = Field(default=None, min_length=1, max_length=50)
