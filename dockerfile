# Usamos Bullseye (Debian 11) para evitar el bloqueo de firmas SHA1
FROM python:3.10-slim-bullseye

# 1. Instalar herramientas del sistema necesarias
RUN apt-get update && apt-get install -y curl gnupg2 apt-transport-https unixodbc-dev

# 2. Registrar el repositorio oficial de Microsoft para Debian 11
RUN curl https://packages.microsoft.com/keys/microsoft.asc | gpg --dearmor -o /usr/share/keyrings/microsoft-prod.gpg \
    && echo "deb [arch=amd64,arm64,armhf signed-by=/usr/share/keyrings/microsoft-prod.gpg] https://packages.microsoft.com/debian/11/prod bullseye main" > /etc/apt/sources.list.d/mssql-release.list

# 3. Actualizar e instalar el driver de SQL Server
RUN apt-get update && ACCEPT_EULA=Y apt-get install -y msodbcsql17

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Comando para arrancar Uvicorn en Render
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]