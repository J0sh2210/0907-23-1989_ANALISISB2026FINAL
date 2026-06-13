FROM python:3.10-slim

# Instalar dependencias del sistema y el driver de Microsoft SQL Server
RUN apt-get update && apt-get install -y curl gnupg2 apt-transport-https unixodbc-dev \
    && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Comando para iniciar la app (el mismo que configuramos antes)
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "80"]