# Historial de Desarrollo - API de Gestión de Incidentes de Red

Este documento contiene la bitácora de los prompts y las iteraciones utilizadas junto con la Inteligencia Artificial (Gemini) para desarrollar el prototipo de la API REST utilizando **FastAPI** y **SQL Server**.

## 1. Planteamiento Inicial y Lógica de Negocio

**Prompt utilizado:**
> "Hola gemini quiero que ACTUES como un Desarrollador de Software, y elabores el siguiente programa Utilzando SQLSERVER y FastAPI. Desarrolla un prototipo de API REST que permita gestionar incidentes de red, implementando las reglas de negocio que se describen a continuación:
> 1. El tiempo máximo de resolución depende de la severidad
> 2. Un técnico no puede tener más de 3 incidentes activos(no cerrado, pueden ser manejados con estado en la DB) simultaneamente
> 3. Los estados SOLAMENTE pueden tener esta direcció: Registrado - Asignado - En progreso - Resuelto - Cerrado
> 4. Un incidente puede ser reasignado a otro técnico, en cualquier momento, El técnico anterior puede liberar el incidente para que otro lo tome.
> 5. Si un incidente CRITICO o URGENTE, lleva más de 2 HORAS sin ser atendido (sin cambiar estado de registrado) debe marcarse como Escalado automáticamente.
> 6. Solo técnicos con especialidad coincidente pueden ser asignados a cierto tipos de incidente
> 7. Debe existir un historial de cambio de estado de incidentes(como bitacora)
> 8. Reportes de incidentes
> Esos son las reglas del negocios, genera el Código de la DB y de la API"

**Resultado:** Generación del script SQL inicial y el archivo `main.py` con la estructura base, modelos de SQLAlchemy y la lógica central de las reglas de negocio (incluyendo la tarea asíncrona para escalar incidentes).

---


## 2. Endpoints de Catálogos y Corrección de Modelos

**Prompt utilizado:**
> "quiero que agregues endpoint para agregar especializaciones, tecnicos, tipos de incidentes"

**Corrección 3 - Atributo faltante en SQLAlchemy:**
Al probar el POST de `IncidentType`, FastAPI arrojó un error 500:
`TypeError: 'Name' is an invalid keyword argument for IncidentType`
* **Solución:** El modelo original en Python no tenía mapeada la columna `Name` que sí existía en la base de datos. Se actualizó el modelo `IncidentType` añadiendo la línea `Name = Column(String)`.

---

## 3. Endpoints de Incidentes y Severidades

**Prompt utilizado (Creación de Incidentes):**
> "ahora de agregar un endpoint para agregar incidentes"

**Prompt utilizado (Severidades y Bitácora):**
> "otro para agregar severidad y que al cambiar el estado agregue en la tabla indicenthistory los datos"

**Corrección 4 - Atributo faltante en Modelo de Incidentes:**
Al intentar registrar un incidente nuevo con su descripción, se presentó un error 500 similar al anterior:
`TypeError: 'Description' is an invalid keyword argument`
* **Solución:** Se agregó la línea `Description = Column(String)` a la clase `Incident` de SQLAlchemy, emparejando el modelo de Python con el script inicial de la base de datos.

---

## 4. Resumen del Proyecto Actual
El proyecto final incluye validaciones robustas con **Pydantic**, mapeo ORM con **SQLAlchemy**, tareas en segundo plano (`BackgroundTasks` / `asyncio`) para cumplimiento de SLA (2 horas para incidentes críticos) y control estricto de transiciones de estados documentados en una bitácora detallada.