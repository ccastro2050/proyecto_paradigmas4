"""
Modelos Pydantic de la entidad ruta — la FRONTERA DE ENTRADA de la API.

Una `ruta` es una direccion protegible del aplicativo: `/facturas`,
`/productos`, `/tablero`. No es una pagina: es el NOMBRE con el que la base
de datos decide quien entra (ver `rutarol`).

Dos cosas que se aprenden en esta tabla:

- El `id` lo genera la base de datos (SERIAL), como en `rol`: el POST no lo
  lleva.
- La columna `ruta` es UNIQUE. Repetirla no es un 400 ni un 422: la base la
  rechaza, y ese rechazo sale como 409 —«choca con lo que ya existe»—, que
  es distinto de «usted escribio mal» (ver 6_contracts.md).
"""

from pydantic import BaseModel, Field


class Ruta(BaseModel):
    """POST /api/ruta — la direccion y para que sirve."""

    ruta: str = Field(min_length=1, max_length=100)
    descripcion: str = Field(min_length=1, max_length=200)


class RutaReemplazo(BaseModel):
    """PUT /api/ruta/{id} — reemplazo COMPLETO.

    Las dos columnas son obligatorias: omitir una es 422. Un PUT que
    conservara lo que no llego seria un PATCH disfrazado.
    """

    ruta: str = Field(min_length=1, max_length=100)
    descripcion: str = Field(min_length=1, max_length=200)


class RutaActualizar(BaseModel):
    """PATCH /api/ruta/{id} — parcial: solo lo que llego."""

    ruta: str | None = Field(default=None, min_length=1, max_length=100)
    descripcion: str | None = Field(default=None, min_length=1, max_length=200)
