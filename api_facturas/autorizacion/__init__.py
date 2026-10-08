"""
El control de acceso de la v3 — las dos puertas y el token.

    jwt_token.py     como se firma y como se lee el token
    dependencias.py  usuario_actual (401) y exige_permiso (403)

La tercera pieza no esta aqui: el PERMISO lo decide la base de datos, con
`verificar_acceso_ruta`. Esta carpeta solo pregunta.
"""
