import sys
from fastapi.testclient import TestClient
from app.main import app
from app.db.session import SessionLocal
from app.core.security import create_access_token
from app.models.employee import Employee, RoleEmployeEnum
from app.models.patient import Patient, SexeEnum
from app.models.groupe import Groupe, TypePlanningEnum
from datetime import date

client = TestClient(app)

def setup_test_db():
    db = SessionLocal()
    # Récupérer l'admin existant ou en créer un avec un numéro unique
    admin = db.query(Employee).filter(Employee.role == RoleEmployeEnum.admin).first()
    if not admin:
        admin = Employee(
            id="admin-test-id",
            nom="Admin",
            prenom="Test",
            telephone="0699999999",
            username="admin_test",
            password_hash="fakehash",
            role=RoleEmployeEnum.admin
        )
        db.add(admin)
        db.commit()
        db.refresh(admin)

    # Récupérer ou créer un patient de test
    patient = db.query(Patient).filter(Patient.id == "patient-test-id").first()
    if not patient:
        patient = Patient(
            id="patient-test-id",
            nom="Dupont",
            prenom="Jean",
            sexe=SexeEnum.masculin,
            date_naissance=date(2016, 5, 10), # 10 ans en 2026
            est_actif=True
        )
        db.add(patient)
        db.commit()

    # Récupérer ou créer un groupe de test
    groupe = db.query(Groupe).filter(Groupe.id == "groupe-test-id").first()
    if not groupe:
        groupe = Groupe(
            id="groupe-test-id",
            nom="Groupe Test",
            type_planning=TypePlanningEnum.fixe
        )
        db.add(groupe)
        db.commit()

    role_val = admin.role.value if hasattr(admin.role, "value") else str(admin.role)
    token = create_access_token({"sub": admin.id, "role": role_val, "id": admin.id})
    admin_id = admin.id
    db.close()
    return token, admin_id

def test_defensive_validation(headers):
    print("--- Testing defensive validation ---")
    
    # 1. Calendrier avec titre vide -> 422
    res = client.post("/api/calendrier", json={"titre": "   ", "date": "2026-08-10"}, headers=headers)
    print(f"POST /api/calendrier (titre='   '): status={res.status_code}")
    assert res.status_code == 422, f"Expected 422, got {res.status_code}: {res.text}"

    # 2. Patient avec nom vide -> 422
    res = client.post("/api/patients", json={"nom": "", "prenom": "Pierre"}, headers=headers)
    print(f"POST /api/patients (nom=''): status={res.status_code}")
    assert res.status_code == 422, f"Expected 422, got {res.status_code}: {res.text}"

    # 3. Groupe avec nom vide -> 422
    res = client.post("/api/groupes", json={"nom": "   ", "type_planning": "fixe"}, headers=headers)
    print(f"POST /api/groupes (nom='   '): status={res.status_code}")
    assert res.status_code == 422, f"Expected 422, got {res.status_code}: {res.text}"

    print("Defensive validation tests passed successfully!")

def test_patient_sexe_age_filtering(headers):
    print("--- Testing patient sexe & age filtering ---")
    
    # 1. Filtre par sexe
    res = client.get("/api/patients?sexe=masculin", headers=headers)
    print(f"GET /api/patients?sexe=masculin: status={res.status_code}, count={len(res.json())}")
    assert res.status_code == 200

    # 2. Filtre par age_min / age_max
    res = client.get("/api/patients?age_min=5&age_max=12", headers=headers)
    print(f"GET /api/patients?age_min=5&age_max=12: status={res.status_code}, count={len(res.json())}")
    assert res.status_code == 200

    print("Patient sexe & age filtering tests passed successfully!")

def test_detail_routes(headers, admin_id):
    print("--- Testing detail routes (GET /api/patients/{id}, groupes/{id}, employees/{id}) ---")
    
    # 1. GET /api/patients/patient-test-id -> 200
    res = client.get("/api/patients/patient-test-id", headers=headers)
    print(f"GET /api/patients/patient-test-id: status={res.status_code}")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"

    # 2. GET /api/groupes/groupe-test-id -> 200
    res = client.get("/api/groupes/groupe-test-id", headers=headers)
    print(f"GET /api/groupes/groupe-test-id: status={res.status_code}")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"

    # 3. GET /api/employees/{admin_id} -> 200
    res = client.get(f"/api/employees/{admin_id}", headers=headers)
    print(f"GET /api/employees/{admin_id}: status={res.status_code}")
    assert res.status_code == 200, f"Expected 200, got {res.status_code}: {res.text}"

    # 4. Inexistent ID -> 404
    res = client.get("/api/patients/non-existent-uuid", headers=headers)
    print(f"GET /api/patients/non-existent-uuid: status={res.status_code}")
    assert res.status_code == 404

    print("Detail routes tests passed successfully!")

if __name__ == "__main__":
    token, admin_id = setup_test_db()
    headers = {"Authorization": f"Bearer {token}"}
    
    test_defensive_validation(headers)
    test_patient_sexe_age_filtering(headers)
    test_detail_routes(headers, admin_id)
    print("\nALL ROUND 2 BACKEND TESTS PASSED!")
