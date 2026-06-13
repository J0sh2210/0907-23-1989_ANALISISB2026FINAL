FROM python:3.10-slim

# 1. Instalar herramientas del sistema necesarias
RUN apt-get update && apt-get install -y curl gnupg2 apt-transport-https unixodbc-dev

# 2. Registrar el repositorio oficial de Microsoft para Debian 12 (Método moderno)
RUN curl -sSL -O https://packages.microsoft.com/config/debian/12/packages-microsoft-prod.deb \
    && dpkg -i packages-microsoft-prod.deb \
    && rm packages-microsoft-prod.deb

# 3. Actualizar los nuevos repositorios e instalar el driver de SQL Server
RUN apt-get update && ACCEPT_EULA=Y apt-get install -y msodbcsql17

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Comando para arrancar Uvicorn en Render
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]