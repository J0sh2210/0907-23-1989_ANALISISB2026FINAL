# Gestión de Incidentes de Red API

## Descripción

API REST desarrollada con FastAPI para la gestión de incidentes de red.

El sistema permite:

* Registrar incidentes.
* Administrar severidades y SLA.
* Gestionar técnicos y especialidades.
* Asignar incidentes a técnicos.
* Controlar transiciones de estados mediante una máquina de estados.
* Registrar historial de cambios.
* Escalar automáticamente incidentes críticos o urgentes.
* Generar reportes de incidentes.
* Ejecutar pruebas unitarias automatizadas.

---

# Tecnologías Utilizadas

* Python 3.10+
* FastAPI
* SQLAlchemy
* SQL Server
* PyODBC
* Pydantic
* Pytest
* HTTPX

---

# Estructura del Proyecto

```text
├── DBCreate.sql
├── main.py
├── requirements.txt
├── test_main.py
└── README.md
```

## Archivos

### DBCreate.sql

Script encargado de crear la base de datos y las tablas necesarias para el funcionamiento del sistema.

Incluye:

* Severities
* Specialties
* Technicians
* IncidentTypes
* Incidents
* IncidentHistory

---

### main.py

Contiene:

* Configuración de FastAPI
* Configuración de SQLAlchemy
* Modelos ORM
* Reglas de negocio
* Endpoints REST
* Escalamiento automático de incidentes
* Gestión de estados
* Gestión de historial

---

### requirements.txt

Lista de dependencias necesarias para ejecutar el proyecto.

---

### test_main.py

Pruebas unitarias utilizando:

* pytest
* FastAPI TestClient
* SQLite en memoria

Permite validar:

* Creación de especialidades
* Creación de severidades
* Creación de incidentes
* Asignación de técnicos
* Validación de especialidades
* Transiciones de estados

---

# Requisitos Previos

## Instalar Python

Versión recomendada:

```bash
Python 3.10 o superior
```

Verificar instalación:

```bash
python --version
```

---

## Instalar SQL Server

Puede utilizar:

* SQL Server Express
* SQL Server Developer

Además debe instalar:

```text
ODBC Driver 17 for SQL Server
```

---

# Configuración de Base de Datos

## 1. Crear la Base de Datos

Ejecutar:

```sql
DBCreate.sql
```

desde:

* SQL Server Management Studio (SSMS)
* Azure Data Studio

---

## 2. Verificar la Cadena de Conexión

En el archivo:

```python
main.py
```

Modificar:

```python
DATABASE_URL = r"mssql+pyodbc://SERVIDOR/NetworkIncidentsDB?driver=ODBC+Driver+17+for+SQL+Server&Trusted_Connection=yes"
```

Ejemplo:

```python
DATABASE_URL = r"mssql+pyodbc://JOSH\SQLEXPRESS/NetworkIncidentsDB?driver=ODBC+Driver+17+for+SQL+Server&Trusted_Connection=yes"
```

Sustituir:

```text
JOSH\SQLEXPRESS
```

por el nombre de su instancia SQL Server.

---

# Instalación

## Crear entorno virtual

Windows:

```bash
python -m venv venv
```

Activar:

```bash
venv\Scripts\activate
```

Linux:

```bash
python3 -m venv venv
source venv/bin/activate
```

---

## Instalar Dependencias

```bash
pip install -r requirements.txt
```

---

# Ejecución del Proyecto

Iniciar servidor FastAPI:

```bash
uvicorn main:app --reload
```

Salida esperada:

```text
INFO: Uvicorn running on http://127.0.0.1:8000
```

---

# Documentación Swagger

FastAPI genera documentación automáticamente.

Acceder a:

```text
http://127.0.0.1:8000/docs
```

También:

```text
http://127.0.0.1:8000/redoc
```

---

# Flujo General del Sistema

## Estados Permitidos

```text
Registrado
   ↓
Asignado
   ↓
En progreso
   ↓
Resuelto
   ↓
Cerrado
```

Estados alternativos:

```text
Registrado → Escalado → Asignado
```

---

# Reglas de Negocio

## Regla 1

Cada severidad posee:

```text
MaxResolutionHours
```

que representa el SLA máximo permitido.

---

## Regla 2

Un técnico puede tener máximo:

```text
3 incidentes activos
```

simultáneamente.

---

## Regla 3

Las transiciones de estado son controladas por una máquina de estados.

No se permiten cambios arbitrarios.

---

## Regla 4

Un técnico puede liberar un incidente.

El incidente vuelve a:

```text
Registrado
```

para ser reasignado.

---

## Regla 5

Escalamiento automático.

Si un incidente:

* es Urgente o Crítico
* permanece Registrado por más de 2 horas

entonces pasa automáticamente a:

```text
Escalado
```

---

## Regla 6

La especialidad del técnico debe coincidir con la especialidad requerida por el tipo de incidente.

---

## Regla 7

Todo cambio queda registrado en:

```text
IncidentHistory
```

---

## Regla 8

El sistema permite consultar reportes filtrando por estado.

---

# Endpoints Principales

## Especialidades

Crear:

```http
POST /specialties/
```

---

## Técnicos

Crear:

```http
POST /technicians/
```

---

## Severidades

Crear:

```http
POST /severities/
```

---

## Tipos de Incidentes

Crear:

```http
POST /incident-types/
```

---

## Incidentes

Registrar:

```http
POST /incidents/
```

---

Asignar técnico:

```http
POST /incidents/assign/{incident_id}
```

---

Liberar incidente:

```http
PUT /incidents/release/{incident_id}
```

---

Actualizar estado:

```http
PUT /incidents/{incident_id}/status
```

---

Consultar historial:

```http
GET /incidents/{incident_id}/history
```

---

Reportes:

```http
GET /reports/incidents
```

---

# Ejecución de Pruebas

Ejecutar todas las pruebas:

```bash
pytest -v
```

Salida esperada:

```text
test_create_specialty PASSED
test_create_severity PASSED
test_create_incident_flow PASSED
test_assign_technician_success PASSED
test_assign_technician_wrong_specialty PASSED
test_invalid_status_transition PASSED
```

---

# Ejemplos de Uso

## Crear Especialidad

```json
{
  "Name": "Redes"
}
```

---

## Crear Técnico

```json
{
  "Name": "Juan Pérez",
  "SpecialtyId": 1
}
```

---

## Crear Severidad

```json
{
  "Name": "Crítico",
  "MaxResolutionHours": 2
}
```

---

## Crear Incidente

```json
{
  "Title": "Caída del servidor principal",
  "Description": "Sin conectividad",
  "SeverityId": 1,
  "TypeId": 1
}
```

---

# Autor

Proyecto desarrollado para la gestión de incidentes de infraestructura y redes utilizando FastAPI, SQLAlchemy y SQL Server.
