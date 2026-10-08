"""
Modelos Pydantic de la tabla puente rutarol — ruta <-> rol.

UNA TABLA PUENTE NO ES UNA ENTIDAD, y sus modelos lo muestran:

- No tiene id propio: su llave primaria son LAS DOS columnas juntas
  (`fkidruta`, `fkidrol`). Una pareja existe o no existe.
- No tiene campos sueltos que actualizar: cambiar una pareja es borrar una e
  insertar otra. Por eso el PUT y el PATCH de este recurso estan escritos
  pero apagados en el controller —con la explicacion al lado—.
- Lo que SI necesita son busquedas POR CADA LADO: «que roles entran a esta
  ruta» y «a que rutas entra este rol». Las dos preguntas son la razon de
  ser de la tabla.
"""

from pydantic import BaseModel, Field


class RutaRolCrear(BaseModel):
    """POST /api/rutarol — la pareja completa; las dos obligatorias.

    `gt=0` no es decoracion: un id 0 o negativo no puede existir en una
    columna SERIAL, y rechazarlo aqui ahorra un viaje a la base de datos
    para que la foranea diga lo mismo mas despacio.
    """

    fkidruta: int = Field(gt=0)
    fkidrol: int = Field(gt=0)


class RutaRolActualizar(BaseModel):
    """Para el PATCH apagado: llega SOLO el lado que se mueve."""

    fkidruta: int | None = Field(default=None, gt=0)
    fkidrol: int | None = Field(default=None, gt=0)


class RutasDeRol(BaseModel):
    """PUT /api/rutarol/rol/{idrol} — las rutas de un rol, de una vez.

    Esta SI esta encendida, y es la operacion que de verdad usa una pantalla
    de permisos: el administrador marca casillas y manda la lista entera.
    Hacerlo con un DELETE y varios POST dejaria al rol sin permisos a mitad
    de camino si algo falla; aqui va todo en una transaccion.
    """

    ids_ruta: list[int] = Field(default_factory=list)
