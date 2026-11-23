# ==============================================================
# API Facturas — FastAPI (puerto 8005)
# En desarrollo, docker-compose monta el código como volumen y
# corre uvicorn con --reload: guardar un archivo recarga solo.
# ==============================================================
FROM python:3.12-slim

# v4 — el driver ODBC de Microsoft: aioodbc (SQL Server async) habla ODBC,
# y el sistema necesita el driver nativo msodbcsql18. PostgreSQL y MariaDB
# no piden nada de esto (sus drivers son Python puro + C embebido) — la
# asimetría también es una lección de motores.
RUN apt-get update && apt-get install -y --no-install-recommends curl gnupg2 unixodbc  && curl -fsSL https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft.gpg  && echo "deb [signed-by=/usr/share/keyrings/microsoft.gpg] https://packages.microsoft.com/debian/12/prod bookworm main" > /etc/apt/sources.list.d/mssql.list  && apt-get update && ACCEPT_EULA=Y apt-get install -y --no-install-recommends msodbcsql18  && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Primero las dependencias: si no cambian, Docker reutiliza esta capa
COPY requirements.txt .
# --default-timeout y --retries: la descarga desde PyPI se corta sola
# en redes lentas y el build falla por red, no por codigo. Con esto
# reintenta en vez de rendirse (se midio: pasa de fallar a pasar).
RUN pip install --no-cache-dir --default-timeout=120 --retries 10 -r requirements.txt

# Después el código (en desarrollo queda tapado por el volumen del compose)
COPY . .

EXPOSE 8005

# EL PUERTO NO LO DECIDE LA APLICACION. En su maquina lo decide este archivo
# (8005) y el compose; publicada, lo IMPONE la plataforma con la variable PORT
# y espera que el programa escuche AHI. Si uno escucha en otro, el hospedaje
# reporta el servicio como caido con la aplicacion viva adentro: es el fallo
# mas comun al publicar en contenedores, y el mas desconcertante.
#
# Por eso el arranque pasa por un shell ("sh", "-c"): la forma corta
# -["uvicorn", ...]- no pasa por shell, y ${PORT} llegaria literal, con el
# signo de dolar incluido. El ${PORT:-8005} dice: use PORT si existe; si no,
# el 8005 de siempre, para que la misma imagen sirva en los dos sitios.
CMD ["sh", "-c", "exec uvicorn main:app --host 0.0.0.0 --port ${PORT:-8005}"]
