from typing import Optional, List, Dict, Any
from datetime import date as date_type, time as time_type
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.seance import Seance, StatutSeanceEnum
from app.models.seance_employe import SeanceEmploye
from app.models.seance_groupe import SeanceGroupe, StatutSeanceGroupeEnum
from app.models.employee import Employee
from app.models.patient import Patient
from app.models.groupe import Groupe


def check_employee_conflict(
    db: Session,
    employee_id: str,
    target_date: date_type,
    heure_debut: time_type,
    heure_fin: time_type,
    exclude_seance_id: Optional[str] = None,
    exclude_seance_groupe_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Vérifie si un employé a déjà une séance (individuelle ou groupe) qui se chevauche
    avec l'intervalle [heure_debut, heure_fin] le jour target_date.

    Condition d'intersection stricte :
        existing.heure_debut < heure_fin AND existing.heure_fin > heure_debut
    Les séances annulées ('annulee') sont exclues car le créneau est libéré.
    """
    if not employee_id or not target_date or not heure_debut or not heure_fin:
        return None

    # Récupérer l'employé pour le nom d'affichage
    emp = db.query(Employee).filter(Employee.id == employee_id).first()
    emp_nom = f"Dr. {emp.prenom} {emp.nom}" if emp else f"Employé {employee_id}"

    # 1. Vérifier les séances individuelles
    query_indiv = (
        db.query(Seance)
        .join(SeanceEmploye, SeanceEmploye.seance_id == Seance.id)
        .filter(
            SeanceEmploye.employe_id == employee_id,
            Seance.date == target_date,
            Seance.statut != StatutSeanceEnum.annulee,
            Seance.heure_debut.isnot(None),
            Seance.heure_fin.isnot(None),
            # Chevauchement d'horaires
            Seance.heure_debut < heure_fin,
            Seance.heure_fin > heure_debut,
        )
    )
    if exclude_seance_id:
        query_indiv = query_indiv.filter(Seance.id != exclude_seance_id)

    conflit_indiv = query_indiv.first()
    if conflit_indiv:
        patient = (
            db.query(Patient).filter(Patient.id == conflit_indiv.patient_id).first()
            if conflit_indiv.patient_id
            else None
        )
        patient_nom = (
            f"{patient.prenom} {patient.nom}" if patient else "Patient"
        )
        debut_str = (
            conflit_indiv.heure_debut.strftime("%H:%M")
            if conflit_indiv.heure_debut
            else "?"
        )
        fin_str = (
            conflit_indiv.heure_fin.strftime("%H:%M")
            if conflit_indiv.heure_fin
            else "?"
        )
        date_str = target_date.strftime("%d/%m/%Y")

        detail = (
            f"Conflit d'horaires : {emp_nom} a déjà une séance individuelle programmée "
            f"le {date_str} de {debut_str} à {fin_str} avec le patient {patient_nom}. "
            f"Impossible de programmer deux séances qui se chevauchent pour le même praticien."
        )
        return {
            "type": "individuelle",
            "employee_id": employee_id,
            "employee_nom": emp_nom,
            "seance_id": conflit_indiv.id,
            "target_date": target_date,
            "date_str": date_str,
            "heure_debut": debut_str,
            "heure_fin": fin_str,
            "conflit_avec": f"Séance individuelle avec {patient_nom}",
            "detail": detail,
        }

    # 2. Vérifier les séances de groupe
    query_groupe = db.query(SeanceGroupe).filter(
        SeanceGroupe.employe_id == employee_id,
        SeanceGroupe.date == target_date,
        SeanceGroupe.statut != StatutSeanceGroupeEnum.annulee,
        SeanceGroupe.heure_debut.isnot(None),
        SeanceGroupe.heure_fin.isnot(None),
        # Chevauchement d'horaires
        SeanceGroupe.heure_debut < heure_fin,
        SeanceGroupe.heure_fin > heure_debut,
    )
    if exclude_seance_groupe_id:
        query_groupe = query_groupe.filter(
            SeanceGroupe.id != exclude_seance_groupe_id
        )

    conflit_groupe = query_groupe.first()
    if conflit_groupe:
        groupe = (
            db.query(Groupe).filter(Groupe.id == conflit_groupe.groupe_id).first()
            if conflit_groupe.groupe_id
            else None
        )
        groupe_nom = groupe.nom if groupe else "Groupe"
        debut_str = (
            conflit_groupe.heure_debut.strftime("%H:%M")
            if conflit_groupe.heure_debut
            else "?"
        )
        fin_str = (
            conflit_groupe.heure_fin.strftime("%H:%M")
            if conflit_groupe.heure_fin
            else "?"
        )
        date_str = target_date.strftime("%d/%m/%Y")

        detail = (
            f"Conflit d'horaires : {emp_nom} a déjà une séance de groupe programmée "
            f"le {date_str} de {debut_str} à {fin_str} pour le groupe « {groupe_nom} ». "
            f"Impossible de programmer deux séances qui se chevauchent pour le même praticien."
        )
        return {
            "type": "groupe",
            "employee_id": employee_id,
            "employee_nom": emp_nom,
            "seance_id": conflit_groupe.id,
            "target_date": target_date,
            "date_str": date_str,
            "heure_debut": debut_str,
            "heure_fin": fin_str,
            "conflit_avec": f"Séance collective groupe « {groupe_nom} »",
            "detail": detail,
        }

    return None


def validate_employees_no_conflict(
    db: Session,
    employee_ids: Optional[List[str]],
    target_date: date_type,
    heure_debut: time_type,
    heure_fin: time_type,
    exclude_seance_id: Optional[str] = None,
    exclude_seance_groupe_id: Optional[str] = None,
) -> None:
    """
    Vérifie qu'aucun des employés spécifiés n'a de conflit sur ce créneau.
    Lève HTTPException(409) avec message explicatif en cas de conflit.
    """
    if not employee_ids or not target_date or not heure_debut or not heure_fin:
        return

    for emp_id in employee_ids:
        if not emp_id:
            continue
        conflit = check_employee_conflict(
            db=db,
            employee_id=emp_id,
            target_date=target_date,
            heure_debut=heure_debut,
            heure_fin=heure_fin,
            exclude_seance_id=exclude_seance_id,
            exclude_seance_groupe_id=exclude_seance_groupe_id,
        )
        if conflit:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=conflit["detail"],
            )
