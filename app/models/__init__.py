# Import all models so SQLAlchemy registers them before create_all()
from app.models.parent import Parent
from app.models.patient import Patient
from app.models.patient_parent import PatientParent
from app.models.employee import Employee
from app.models.dossier_medical import DossierMedical
from app.models.employee_patient_access import EmployeePatientAccess
from app.models.groupe import Groupe
from app.models.groupe_planning_recurrent import GroupePlanningRecurrent
from app.models.patient_groupe import PatientGroupe
from app.models.seance import Seance
from app.models.seance_employe import SeanceEmploye
from app.models.patient_planning_recurrent import PatientPlanningRecurrent
from app.models.seance_groupe import SeanceGroupe
from app.models.seance_groupe_participant import SeanceGroupeParticipant
from app.models.plan_therapeutique import PlanTherapeutique
from app.models.etape_plan_therapeutique import EtapePlanTherapeutique
from app.models.tache import Tache
from app.models.evenement_calendrier import EvenementCalendrier
from app.models.note_patient import NotePatient

__all__ = [
    "Parent",
    "Patient",
    "PatientParent",
    "Employee",
    "DossierMedical",
    "EmployeePatientAccess",
    "Groupe",
    "GroupePlanningRecurrent",
    "PatientGroupe",
    "Seance",
    "SeanceEmploye",
    "PatientPlanningRecurrent",
    "SeanceGroupe",
    "SeanceGroupeParticipant",
    "PlanTherapeutique",
    "EtapePlanTherapeutique",
    "Tache",
    "EvenementCalendrier",
    "NotePatient",
]
