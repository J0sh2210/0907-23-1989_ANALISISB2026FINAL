import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Importamos tu app y modelos desde main.py
from main import app, Base, get_db

# --- CONFIGURACIÓN DEL MOCK DE LA BASE DE DATOS ---
# Usamos SQLite en memoria. Es rápido, no requiere servidor y se destruye al terminar.
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Sobrescribimos la dependencia original para que use nuestra BD de pruebas
def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

# Creamos el cliente de pruebas
client = TestClient(app)

# --- FIXTURES DE PYTEST ---
# Esto se ejecuta antes de cada prueba para asegurar que la BD esté limpia
@pytest.fixture(autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

# --- PRUEBAS UNITARIAS ---

def test_create_specialty():
    response = client.post("/specialties/", json={"Name": "Redes"})
    assert response.status_code == 201
    assert response.json()["data"]["Name"] == "Redes"
    assert "Id" in response.json()["data"]

def test_create_severity():
    response = client.post("/severities/", json={"Name": "Alta", "MaxResolutionHours": 4})
    assert response.status_code == 201
    assert response.json()["data"]["Name"] == "Alta"
    assert response.json()["data"]["MaxResolutionHours"] == 4

# Asegúrate de que tus importaciones incluyan 'Incident' y 'TestingSessionLocal'
from main import app, Base, get_db, Incident 

# ... (resto de tu código de configuración) ...

def test_create_incident_flow():
    """
    Prueba el flujo completo: Crear especialidad, tipo, severidad y finalmente el incidente.
    """
    # 1. Crear Especialidad
    client.post("/specialties/", json={"Name": "Seguridad"})
    
    # 2. Crear Tipo de Incidente
    client.post("/incident-types/", json={"Name": "Ataque DDoS", "SpecialtyId": 1})
    
    # 3. Crear Severidad
    client.post("/severities/", json={"Name": "Crítico", "MaxResolutionHours": 1})
    
    # 4. Crear Incidente
    response = client.post("/incidents/", json={
        "Title": "Caída del servidor principal",
        "Description": "Tráfico inusual detectado",
        "SeverityId": 1,
        "TypeId": 1
    })
    
    # Validamos que el endpoint respondió exitosamente
    assert response.status_code == 201
    assert "exitosamente" in response.json()["message"]
    
    # 5. Validación robusta: Consultar directamente la BD de pruebas
    db = TestingSessionLocal()
    try:
        incident_in_db = db.query(Incident).filter(Incident.Id == 1).first()
        
        # Validamos que realmente se guardó y tiene los datos correctos
        assert incident_in_db is not None
        assert incident_in_db.Title == "Caída del servidor principal"
        assert incident_in_db.Status == "Registrado" # Regla del estado inicial
    finally:
        db.close()
def test_assign_technician_success():
    """
    Verifica que la asignación de un técnico funcione y respete la especialidad.
    """
    # Preparar el entorno (Mock data)
    client.post("/specialties/", json={"Name": "Telecomunicaciones"})
    client.post("/technicians/", json={"Name": "Juan Pérez", "SpecialtyId": 1})
    client.post("/incident-types/", json={"Name": "Corte de Fibra", "SpecialtyId": 1})
    client.post("/severities/", json={"Name": "Media", "MaxResolutionHours": 8})
    client.post("/incidents/", json={
        "Title": "Sin conexión en piso 3",
        "Description": "Falla de switch",
        "SeverityId": 1,
        "TypeId": 1
    })

    # Asignar técnico 1 al incidente 1
    response = client.post("/incidents/assign/1?technician_id=1")
    
    assert response.status_code == 200
    assert response.json()["message"] == "Incidente asignado correctamente"
    
    # Validar el historial (Regla 7)
    history_response = client.get("/incidents/1/history")
    history = history_response.json()
    assert len(history) == 2 # Registro inicial + Asignación
    assert history[-1]["NewStatus"] == "Asignado"

def test_assign_technician_wrong_specialty():
    """
    Regla 6: Falla al asignar si el técnico no tiene la especialidad correcta.
    """
    client.post("/specialties/", json={"Name": "Redes"})
    client.post("/specialties/", json={"Name": "Bases de Datos"})
    
    # Técnico de Bases de Datos (Id 2)
    client.post("/technicians/", json={"Name": "Ana", "SpecialtyId": 2})
    
    # Incidente de Redes (Id 1)
    client.post("/incident-types/", json={"Name": "Corte de router", "SpecialtyId": 1})
    client.post("/severities/", json={"Name": "Baja", "MaxResolutionHours": 24})
    client.post("/incidents/", json={"Title": "Falla en router", "SeverityId": 1, "TypeId": 1})

    # Intentar asignar a Ana (BD) a un problema de Redes
    response = client.post("/incidents/assign/1?technician_id=1")
    
    assert response.status_code == 400
    assert "especialidad del técnico no coincide" in response.json()["detail"]

def test_invalid_status_transition():
    """
    Regla 3: Falla si se intenta hacer una transición de estado no permitida.
    """
    # Configuración rápida
    client.post("/specialties/", json={"Name": "General"})
    client.post("/incident-types/", json={"Name": "Otro", "SpecialtyId": 1})
    client.post("/severities/", json={"Name": "Baja", "MaxResolutionHours": 12})
    client.post("/incidents/", json={"Title": "Prueba", "SeverityId": 1, "TypeId": 1})

    # El estado actual es "Registrado". Intentaremos pasar a "Resuelto" directo (Inválido)
    response = client.put("/incidents/1/status?new_status=Resuelto")
    
    assert response.status_code == 400
    assert "No se puede pasar" in response.json()["detail"]