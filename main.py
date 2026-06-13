from fastapi import FastAPI, HTTPException, Depends, BackgroundTasks
from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime, text
from sqlalchemy.orm import declarative_base, sessionmaker, Session, relationship
from pydantic import BaseModel
from datetime import datetime, timedelta
import asyncio

# --- CONFIGURACIÓN DE BASE DE DATOS ---
# Asegúrate de configurar tu cadena de conexión a SQL Server
DATABASE_URL = r"mssql+pyodbc://JOSH\SQLEXPRESS/NetworkIncidentsDB?driver=ODBC+Driver+17+for+SQL+Server&Trusted_Connection=yes"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# --- MODELOS SQLALCHEMY ---

class SeverityCreate(BaseModel):
    Name: str  # Ej: Baja, Media, Alta, Urgente, Crítico
    MaxResolutionHours: int  # Regla 1: Tiempo máximo en horas

class IncidentStatusUpdate(BaseModel):
    NewStatus: str  # El nuevo estado al que se quiere pasar
    ChangedBy: str | None = None  # Quién realiza el cambio (Ej: "Operador JOSH")
    Notes: str | None = None  # Comentarios de por qué se cambia el estado

class Incident(Base):
    __tablename__ = "Incidents"
    Id = Column(Integer, primary_key=True, index=True)
    Title = Column(String)
    Description = Column(String)
    Status = Column(String, default="Registrado")
    SeverityId = Column(Integer, ForeignKey("Severities.Id"))
    TypeId = Column(Integer, ForeignKey("IncidentTypes.Id"))
    TechnicianId = Column(Integer, ForeignKey("Technicians.Id"), nullable=True)
    CreatedAt = Column(DateTime, default=datetime.utcnow)
    UpdatedAt = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Technician(Base):
    __tablename__ = "Technicians"
    Id = Column(Integer, primary_key=True, index=True)
    Name = Column(String)
    SpecialtyId = Column(Integer)

class IncidentType(Base):
    __tablename__ = "IncidentTypes"
    Id = Column(Integer, primary_key=True, index=True)
    Name = Column(String) # <--- ¡Esta es la línea que falta!
    SpecialtyId = Column(Integer)

class Severity(Base):
    __tablename__ = "Severities"
    Id = Column(Integer, primary_key=True, index=True)
    Name = Column(String)
    MaxResolutionHours = Column(Integer)

class IncidentHistory(Base):
    __tablename__ = "IncidentHistory"
    Id = Column(Integer, primary_key=True, index=True)
    IncidentId = Column(Integer, ForeignKey("Incidents.Id"))
    OldStatus = Column(String, nullable=True)
    NewStatus = Column(String)
    ChangedAt = Column(DateTime, default=datetime.utcnow)

class IncidentCreate(BaseModel):
    Title: str
    Description: str | None = None
    SeverityId: int
    TypeId: int

# --- DEPENDENCIAS ---
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# --- FASTAPI APP ---
app = FastAPI(title="Gestión de Incidentes de Red API")

# --- MÁQUINA DE ESTADOS (Regla 3 y 4) ---
# Define hacia qué estados puede transicionar un estado actual
VALID_TRANSITIONS = {
    "Registrado": ["Asignado", "Escalado"],
    "Asignado": ["En progreso", "Registrado"], # Puede volver a Registrado si el técnico lo libera (Regla 4)
    "En progreso": ["Resuelto", "Asignado"], # Puede reasignarse
    "Resuelto": ["Cerrado", "En progreso"], # Puede reabrirse si falló
    "Cerrado": [],
    "Escalado": ["Asignado"]
}

# --- TAREA EN SEGUNDO PLANO (Regla 5) ---
async def check_escalations():
    """Revisa incidentes Críticos/Urgentes sin atender por más de 2 horas."""
    while True:
        db = SessionLocal()
        try:
            # Buscamos incidentes en estado 'Registrado' con severidad alta (ej. IDs 4 y 5 para Urgente/Critico)
            cutoff_time = datetime.utcnow() - timedelta(hours=2)
            incidents_to_escalate = db.query(Incident).join(Severity).filter(
                Incident.Status == "Registrado",
                Severity.Name.in_(["Urgente", "Crítico"]),
                Incident.CreatedAt <= cutoff_time
            ).all()

            for inc in incidents_to_escalate:
                # Actualizar historial (Regla 7)
                history = IncidentHistory(IncidentId=inc.Id, OldStatus=inc.Status, NewStatus="Escalado")
                db.add(history)
                # Cambiar estado
                inc.Status = "Escalado"
                inc.UpdatedAt = datetime.utcnow()
            
            db.commit()
        finally:
            db.close()
        await asyncio.sleep(300) # Revisa cada 5 minutos

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(check_escalations())

# --- ENDPOINTS ---

@app.post("/incidents/assign/{incident_id}")
def assign_technician(incident_id: int, technician_id: int, db: Session = Depends(get_db)):
    incident = db.query(Incident).filter(Incident.Id == incident_id).first()
    technician = db.query(Technician).filter(Technician.Id == technician_id).first()
    
    if not incident or not technician:
        raise HTTPException(status_code=404, detail="Incidente o Técnico no encontrado")

    # Regla 2: Máximo 3 incidentes activos
    active_incidents = db.query(Incident).filter(
        Incident.TechnicianId == technician_id,
        Incident.Status.notin_(["Cerrado", "Resuelto"]) # Consideramos activos los que no están cerrados/resueltos
    ).count()

    if active_incidents >= 3:
        raise HTTPException(status_code=400, detail="El técnico ya tiene el máximo de 3 incidentes activos.")

    # Regla 6: Validar especialidad
    inc_type = db.query(IncidentType).filter(IncidentType.Id == incident.TypeId).first()
    if inc_type.SpecialtyId != technician.SpecialtyId:
        raise HTTPException(status_code=400, detail="La especialidad del técnico no coincide con el tipo de incidente.")

    # Regla 3 y 4: Cambio de estado y reasignación
    old_status = incident.Status
    new_status = "Asignado"

    if new_status not in VALID_TRANSITIONS.get(old_status, []):
        raise HTTPException(status_code=400, detail=f"Transición inválida de {old_status} a {new_status}")

    incident.TechnicianId = technician_id
    incident.Status = new_status
    
    # Regla 7: Guardar en bitácora
    history = IncidentHistory(IncidentId=incident.Id, OldStatus=old_status, NewStatus=new_status)
    db.add(history)
    db.commit()

    return {"message": "Incidente asignado correctamente"}

@app.put("/incidents/release/{incident_id}")
def release_incident(incident_id: int, db: Session = Depends(get_db)):
    """Regla 4: El técnico anterior libera el incidente para que otro lo tome."""
    incident = db.query(Incident).filter(Incident.Id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incidente no encontrado")
    
    old_status = incident.Status
    incident.TechnicianId = None
    incident.Status = "Registrado" # Vuelve a la piscina
    
    history = IncidentHistory(IncidentId=incident.Id, OldStatus=old_status, NewStatus="Registrado")
    db.add(history)
    db.commit()
    
    return {"message": "Incidente liberado exitosamente"}

@app.put("/incidents/{incident_id}/status")
def update_status(incident_id: int, new_status: str, db: Session = Depends(get_db)):
    incident = db.query(Incident).filter(Incident.Id == incident_id).first()
    if not incident:
        raise HTTPException(status_code=404, detail="Incidente no encontrado")

    old_status = incident.Status

    # Regla 3: Validar dirección del estado
    if new_status not in VALID_TRANSITIONS.get(old_status, []):
        raise HTTPException(status_code=400, detail=f"No se puede pasar de '{old_status}' a '{new_status}'. Revisa el flujo de estados.")

    incident.Status = new_status
    
    # Regla 7: Guardar en bitácora
    history = IncidentHistory(IncidentId=incident.Id, OldStatus=old_status, NewStatus=new_status)
    db.add(history)
    db.commit()

    return {"message": f"Estado actualizado a {new_status}"}

@app.get("/reports/incidents")
def get_incident_report(status: str = None, db: Session = Depends(get_db)):
    """Regla 8: Reportes de incidentes."""
    query = db.query(Incident)
    if status:
        query = query.filter(Incident.Status == status)
    
    incidents = query.all()
    return incidents

@app.get("/incidents/{incident_id}/history")
def get_incident_history(incident_id: int, db: Session = Depends(get_db)):
    """Regla 7: Ver bitácora."""
    history = db.query(IncidentHistory).filter(IncidentHistory.IncidentId == incident_id).order_by(IncidentHistory.ChangedAt.asc()).all()
    return history

# --- FALTANTES EN MODELOS SQLALCHEMY ---
class Specialty(Base):
    __tablename__ = "Specialties"
    Id = Column(Integer, primary_key=True, index=True)
    Name = Column(String)


class SpecialtyCreate(BaseModel):
    Name: str

class TechnicianCreate(BaseModel):
    Name: str
    SpecialtyId: int

class IncidentTypeCreate(BaseModel):
    Name: str
    SpecialtyId: int


# --- ENDPOINTS DE CATÁLOGOS ---

@app.post("/specialties/", status_code=201)
def create_specialty(specialty: SpecialtyCreate, db: Session = Depends(get_db)):
    """Crea una nueva especialidad."""
    db_specialty = Specialty(Name=specialty.Name)
    db.add(db_specialty)
    db.commit()
    db.refresh(db_specialty)
    return {"message": "Especialidad creada", "data": db_specialty}

@app.post("/technicians/", status_code=201)
def create_technician(technician: TechnicianCreate, db: Session = Depends(get_db)):
    """Crea un nuevo técnico, validando que la especialidad exista."""
    # Validar que la especialidad exista
    db_specialty = db.query(Specialty).filter(Specialty.Id == technician.SpecialtyId).first()
    if not db_specialty:
        raise HTTPException(status_code=404, detail="La especialidad indicada no existe")

    db_technician = Technician(Name=technician.Name, SpecialtyId=technician.SpecialtyId)
    db.add(db_technician)
    db.commit()
    db.refresh(db_technician)
    return {"message": "Técnico creado", "data": db_technician}

@app.post("/incident-types/", status_code=201)
def create_incident_type(incident_type: IncidentTypeCreate, db: Session = Depends(get_db)):
    """Crea un tipo de incidente, validando que la especialidad exista."""
    # Validar que la especialidad exista
    db_specialty = db.query(Specialty).filter(Specialty.Id == incident_type.SpecialtyId).first()
    if not db_specialty:
        raise HTTPException(status_code=404, detail="La especialidad indicada no existe")

    db_incident_type = IncidentType(Name=incident_type.Name, SpecialtyId=incident_type.SpecialtyId)
    db.add(db_incident_type)
    db.commit()
    db.refresh(db_incident_type)
    return {"message": "Tipo de incidente creado", "data": db_incident_type}

@app.post("/incidents/", status_code=201)
def create_incident(incident: IncidentCreate, db: Session = Depends(get_db)):
    """
    Crea un nuevo incidente de red con estado inicial 'Registrado' 
    y genera su primer registro en la bitácora.
    """
    # 1. Validar que la Severidad exista en la base de datos
    db_severity = db.query(Severity).filter(Severity.Id == incident.SeverityId).first()
    if not db_severity:
        raise HTTPException(status_code=404, detail="La severidad indicada no existe")

    # 2. Validar que el Tipo de Incidente exista en la base de datos
    db_type = db.query(IncidentType).filter(IncidentType.Id == incident.TypeId).first()
    if not db_type:
        raise HTTPException(status_code=404, detail="El tipo de incidente indicado no existe")

    # 3. Crear la instancia del incidente (Por defecto el estado es 'Registrado' gracias al modelo SQLALchemy)
    db_incident = Incident(
        Title=incident.Title,
        Description=incident.Description,
        SeverityId=incident.SeverityId,
        TypeId=incident.TypeId,
        Status="Registrado" # Forzamos el estado inicial de la regla de negocio
    )
    
    db.add(db_incident)
    db.commit() # Guardamos para obtener el Id generado por SQL Server
    db.refresh(db_incident)

    # 4. Regla 7: Crear el historial / bitácora inicial del incidente
    db_history = IncidentHistory(
        IncidentId=db_incident.Id,
        OldStatus=None,
        NewStatus="Registrado"
    )
    db.add(db_history)
    db.commit()

    return {
        "message": "Incidente registrado exitosamente en el sistema",
        "data": db_incident
    }

@app.post("/severities/", status_code=201)
def create_severity(severity: SeverityCreate, db: Session = Depends(get_db)):
    """Crea una nueva severidad con su respectivo tiempo máximo de resolución (SLA)."""
    db_severity = Severity(
        Name=severity.Name, 
        MaxResolutionHours=severity.MaxResolutionHours
    )
    db.add(db_severity)
    db.commit()
    db.refresh(db_severity)
    return {"message": "Severidad creada con éxito", "data": db_severity}