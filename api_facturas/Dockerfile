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
RUN pip install --no-cache-dir -r requirements.txt

# Después el código (en desarrollo queda tapado por el volumen del compose)
COPY . .

EXPOSE 8005

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8005"]
