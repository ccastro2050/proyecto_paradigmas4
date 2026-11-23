# ============================================================
# El FRONT en Flask + Jinja2.
#
# Es un CONTENEDOR APARTE de la API, y eso es lo que se quiere demostrar: la
# interfaz y la API son dos procesos distintos que se hablan por HTTP. Apague
# la API y la interfaz sigue en pie, con su aviso y sin una sola fila.
#
# `slim` y no la imagen completa: son ~50 MB contra ~350 MB, y lo unico que
# hace falta es Python y dos paquetes.
# ============================================================
FROM python:3.12-slim

WORKDIR /app

# Los requisitos PRIMERO y el codigo despues: asi Docker reusa la capa de los
# paquetes mientras `requirements.txt` no cambie, y reconstruir tras editar un
# .py tarda segundos en vez de minutos.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PUERTO=8046
EXPOSE 8046

# El defecto de la IMAGEN es publicado, no desarrollo: asi un hospedaje que
# solo haga build + run arranca con gunicorn sin que nadie configure nada.
# El modo comodo se pide a proposito (el compose pone DEPURAR=1).
ENV DEPURAR=0

# UN SOLO ARRANQUE PARA LOS DOS MUNDOS: con DEPURAR=0 arranca gunicorn -un
# servidor de verdad, que atiende varias peticiones a la vez-; con DEPURAR=1,
# el de Flask, que recarga al guardar. Y ${PORT:-${PUERTO:-8046}} es la misma
# cadena de respaldo del app.py: manda el puerto que imponga la plataforma.
CMD ["sh", "-c", "if [ \"$DEPURAR\" = \"0\" ]; then exec gunicorn --bind 0.0.0.0:${PORT:-${PUERTO:-8046}} --workers 2 app:app; else exec python app.py; fi"]
