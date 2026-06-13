# Historias de Usuario - Gestión de Incidentes de Red

## 1. Registro de incidentes de red

Como operador quiero poder registrar los nuevos incidentes de red que se reporten.

Datos:

* Título del incidente
* Descripción
* ID de la Severidad
* ID del Tipo de incidente

Criterios de aceptación:

* El incidente debe guardarse obligatoriamente con el estado inicial "Registrado".
* Los datos ingresados deben guardarse y generar automáticamente el primer registro en la tabla de historial (bitácora).

---

## 2. Asignación de incidentes

Como coordinador quiero poder asignar un incidente registrado a un técnico en específico.

Datos:

* ID del incidente
* ID del técnico

Criterios de aceptación:

* El estado del incidente debe cambiar de "Registrado" o "Escalado" a "Asignado".
* El cambio debe quedar registrado en la bitácora de historial.

---

## 3. Límite de carga de trabajo de técnicos

Como sistema quiero validar la cantidad de incidentes activos de un técnico antes de asignarle uno nuevo para evitar sobrecargas.

Datos:

* ID del técnico
* Estado de los incidentes actuales del técnico

Criterios de aceptación:

* El sistema debe rechazar la asignación si el técnico ya tiene 3 incidentes activos.
* Se considera "activo" cualquier incidente que no esté en estado "Resuelto" o "Cerrado".

---

## 4. Validación de especialidad técnica

Como sistema quiero validar que el técnico tenga la especialidad requerida por el incidente antes de ser asignado.

Datos:

* ID del técnico (y su especialidad)
* ID del incidente (y su tipo/especialidad requerida)

Criterios de aceptación:

* La asignación solo debe ser exitosa si la especialidad del técnico coincide exactamente con la especialidad requerida por el tipo de incidente.

---

## 5. Liberación de incidentes

Como técnico quiero poder liberar un incidente que tengo asignado para que pueda ser tomado por otro técnico.

Datos:

* ID del incidente

Criterios de aceptación:

* El incidente debe cambiar su estado de vuelta a "Registrado".
* El campo del técnico asignado debe limpiarse (quedar nulo).
* La acción de liberación debe quedar guardada en el historial de cambios.

---

## 6. Actualización de estado de incidentes

Como técnico quiero poder actualizar el estado de los incidentes que estoy trabajando para reflejar su avance.

Datos:

* ID del incidente
* Nuevo estado
* Nombre de quien realiza el cambio
* Notas o comentarios

Criterios de aceptación:

* El sistema solo debe permitir transiciones válidas (ej. de Asignado a En progreso, de En progreso a Resuelto).
* Todos los datos, incluyendo el usuario y las notas, deben registrarse en la bitácora.

---

## 7. Escalamiento automático por SLA

Como sistema quiero escalar automáticamente los incidentes urgentes o críticos que no sean atendidos a tiempo.

Datos:

* Fecha y hora de creación del incidente
* Severidad del incidente
* Estado actual

Criterios de aceptación:

* Si un incidente es "Crítico" o "Urgente" y lleva más de 2 horas en estado "Registrado", su estado debe cambiar a "Escalado".
* Este proceso debe realizarse automáticamente en segundo plano y quedar registrado en la bitácora.

---

## 8. Consulta de bitácora (Historial)

Como auditor quiero poder consultar el historial de cambios de estado de un incidente específico.

Datos:

* ID del incidente

Criterios de aceptación:

* El sistema debe devolver una lista cronológica con los estados anteriores, estados nuevos, fecha del cambio, usuario que lo realizó y las notas justificativas.

---

## 9. Reportes de incidentes

Como gerente quiero poder generar reportes de los incidentes del sistema para métricas de rendimiento.

Datos:

* Estado del incidente (Filtro opcional)

Criterios de aceptación:

* Si se provee un estado, el sistema debe retornar solo los incidentes que coincidan.
* Si no se provee filtro, debe retornar la lista completa de incidentes guardados.

---

## 10. Gestión de catálogos base (Severidades)

Como administrador quiero poder registrar los niveles de severidad y sus tiempos máximos de resolución.

Datos:

* Nombre de la severidad (Ej. Baja, Alta, Crítica)
* Horas máximas de resolución (SLA)

Criterios de aceptación:

* Las severidades ingresadas deben ser guardadas, poder ser accesibles y estar disponibles al momento de registrar un nuevo incidente.