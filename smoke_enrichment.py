"""
Smoke test temporaire — vérifie que :
  1. l'enrichissement des réponses n'est pas supprimé par `response_model`,
  2. les nouveaux filtres ?query sont réellement appliqués (plus ignorés),
  3. les 3 nouveaux endpoints groupes répondent,
  4. les schémas Response ne rejouent plus les règles de rejet d'entrée.

Crée ses propres séances / séances de groupe puis les supprime : la base
retrouve son état initial. À supprimer après vérification.
"""
import json
from fastapi.testclient import TestClient
from app.main import app

c = TestClient(app)
OK, KO = "OK  ", "ECHEC"
resultats = []


def verifie(libelle, condition, detail=""):
    resultats.append((bool(condition), libelle))
    print(f"  {OK if condition else KO} {libelle}" + (f"  {detail}" if detail else ""))


r = c.post("/api/auth/login", json={"username": "psy", "password": "samiyapsy"})
token = r.json()["access_token"]
H = {"Authorization": f"Bearer {token}"}
print(f"login: {r.status_code}")


def get(path):
    r = c.get(path, headers=H)
    try:
        return r.status_code, r.json()
    except ValueError:
        return r.status_code, r.text


def n_of(data):
    return len(data) if isinstance(data, list) else "?"


# ─── 1. Toutes les listes répondent 200 (plus de 500 ResponseValidationError) ──
print("\n--- 1. LISTES : STATUT 200 ---")
for path in ["/api/seances", "/api/taches", "/api/groupes", "/api/seances-groupe",
             "/api/parents", "/api/employees", "/api/calendrier", "/api/patients"]:
    code, data = get(path)
    verifie(f"GET {path:22} -> {code}", code == 200, f"n={n_of(data)}")

# L'événement au titre vide en base doit être renvoyé, pas faire tomber la liste
code, evts = get("/api/calendrier")
vides = [e for e in evts if isinstance(e, dict) and not (e.get("titre") or "").strip()] if isinstance(evts, list) else []
verifie("l'evenement au titre vide est renvoye au lieu de casser la liste", bool(vides),
        f"({len(vides)} ligne(s) au titre vide tolerees)")

# ─── 2. Jeu de données temporaire ─────────────────────────────────────────────
print("\n--- 2. CREATION DU JEU DE DONNEES TEMPORAIRE ---")
a_nettoyer = []
code, patients = get("/api/patients?limit=2")
code, groupes = get("/api/groupes?limit=1")
code, employes = get("/api/employees?limit=1")
pid = patients[0]["id"] if patients else None
attendu_nom = f"{patients[0]['prenom']} {patients[0]['nom']}" if patients else None
gid = groupes[0]["id"] if groupes else None
eid = employes[0]["id"] if employes else None

seance_id = None
if pid:
    r = c.post("/api/seances", headers=H, json={
        "patient_id": pid, "date": "2031-03-04", "heure_debut": "10:00:00",
        "heure_fin": "11:00:00", "statut": "prevue",
    })
    verifie("POST /api/seances (planifier une seance individuelle)", r.status_code == 201, str(r.status_code))
    if r.status_code == 201:
        seance_id = r.json()["id"]
        a_nettoyer.append(("/api/seances/" + seance_id, "seance"))

sg_id = None
if gid:
    r = c.post("/api/seances-groupe", headers=H, json={
        "groupe_id": gid, "employe_id": eid, "date": "2031-03-05",
        "heure_debut": "14:00:00", "heure_fin": "15:00:00", "statut": "prevue",
    })
    verifie("POST /api/seances-groupe (planifier une seance de groupe)", r.status_code == 201, str(r.status_code))
    if r.status_code == 201:
        sg_id = r.json()["id"]
        a_nettoyer.append(("/api/seances-groupe/" + sg_id, "seance de groupe"))

# ─── 3. Enrichissement vérifié sur données réelles ────────────────────────────
print("\n--- 3. ENRICHISSEMENT (contenu imbrique, pas seulement declare) ---")
if seance_id:
    code, s = get(f"/api/seances/{seance_id}")
    p = s.get("patient") if isinstance(s, dict) else None
    verifie("SeanceResponse.patient est un objet avec nom+prenom", isinstance(p, dict) and p.get("nom"),
            json.dumps(p, ensure_ascii=False))
    code, liste = get("/api/seances?limit=50")
    trouvee = next((x for x in liste if x["id"] == seance_id), None) if isinstance(liste, list) else None
    verifie("patient present aussi dans la LISTE des seances",
            isinstance(trouvee, dict) and isinstance(trouvee.get("patient"), dict))

if sg_id:
    code, s = get(f"/api/seances-groupe/{sg_id}")
    parts = s.get("participants") or [] if isinstance(s, dict) else []
    verifie("SeanceGroupeResponse.groupe est un objet", isinstance(s.get("groupe"), dict),
            json.dumps(s.get("groupe"), ensure_ascii=False))
    verifie("SeanceGroupeResponse.employe est un objet", isinstance(s.get("employe"), dict),
            json.dumps(s.get("employe"), ensure_ascii=False))
    verifie("employe imbrique n'expose PAS password_hash",
            not (isinstance(s.get("employe"), dict) and "password_hash" in s["employe"]))
    verifie("participants auto-crees depuis les membres du groupe", len(parts) > 0, f"n={len(parts)}")
    if parts:
        verifie("participants[].patient est un objet avec nom",
                isinstance(parts[0].get("patient"), dict) and parts[0]["patient"].get("nom"),
                json.dumps(parts[0].get("patient"), ensure_ascii=False))
        # US : mettre a jour la presence et le suivi d'un participant avec medias
        ppid = parts[0]["patient_id"]
        r = c.patch(f"/api/seances-groupe/{sg_id}/participants/{ppid}", headers=H, json={
            "statut_presence": "present", "description_etat": "smoke test",
            "medias": ["/uploads/smoke.jpg"],
        })
        verifie("PATCH participant (presence + suivi + medias)", r.status_code == 200, str(r.status_code))
        if r.status_code == 200:
            b = r.json()
            verifie("la reponse du PATCH participant contient patient imbrique", isinstance(b.get("patient"), dict))
            verifie("medias conserves sur le participant", b.get("medias") == ["/uploads/smoke.jpg"], str(b.get("medias")))

code, taches = get("/api/taches?limit=5")
if isinstance(taches, list) and taches:
    avec_pat = [t for t in taches if isinstance(t.get("patient"), dict)]
    avec_emp = [t for t in taches if isinstance(t.get("assigne_employee"), dict)]
    verifie("TacheResponse.patient / assigne_employee imbriques",
            avec_pat or avec_emp, f"patient={len(avec_pat)}/{len(taches)} employe={len(avec_emp)}/{len(taches)}")

if gid:
    code, g = get(f"/api/groupes/{gid}")
    verifie("GroupeResponse.patients imbriques", isinstance(g.get("patients"), list), f"n={n_of(g.get('patients'))}")
    verifie("GroupeResponse.planning_recurrent imbrique", isinstance(g.get("planning_recurrent"), list),
            f"n={n_of(g.get('planning_recurrent'))}")
    verifie("GroupeResponse.employees imbriques", isinstance(g.get("employees"), list), f"n={n_of(g.get('employees'))}")

# ─── 4. Nouveaux endpoints groupes ────────────────────────────────────────────
print("\n--- 4. NOUVEAUX ENDPOINTS GROUPES ---")
if gid:
    code, membres = get(f"/api/groupes/{gid}/patients")
    verifie(f"GET  /api/groupes/{{id}}/patients -> {code}", code == 200, f"n={n_of(membres)}")
    code, plan = get(f"/api/groupes/{gid}/planning-recurrent")
    verifie(f"GET  /api/groupes/{{id}}/planning-recurrent -> {code}", code == 200, f"n={n_of(plan)}")
    r = c.delete(f"/api/groupes/{gid}/patients/uuid-inexistant", headers=H)
    verifie("DELETE /api/groupes/{id}/patients/{pid} inconnu -> 404 (plus 405)", r.status_code == 404, str(r.status_code))
    # Aller-retour reel : ajout puis retrait d'un patient
    if len(patients) > 1:
        p2 = patients[1]["id"]
        deja = any(m.get("id") == p2 for m in (membres or []))
        if not deja:
            r = c.post(f"/api/groupes/{gid}/patients", headers=H, json={"patient_id": p2})
            verifie("POST  ajout d'un patient au groupe", r.status_code in (200, 201), str(r.status_code))
            code, apres = get(f"/api/groupes/{gid}/patients")
            verifie("le patient ajoute apparait dans les membres", any(m.get("id") == p2 for m in apres))
            r = c.delete(f"/api/groupes/{gid}/patients/{p2}", headers=H)
            verifie("DELETE retrait du patient du groupe", r.status_code == 204, str(r.status_code))
            code, final = get(f"/api/groupes/{gid}/patients")
            verifie("le patient retire a bien disparu", not any(m.get("id") == p2 for m in final))

# ─── 5. Filtres réellement appliqués ──────────────────────────────────────────
print("\n--- 5. FILTRES (doivent changer le resultat, plus etre ignores) ---")
comparaisons = [
    ("parents ?search=zzzzzzzz", "/api/parents", "/api/parents?search=zzzzzzzz"),
    ("employees ?search=zzzzzzzz", "/api/employees", "/api/employees?search=zzzzzzzz"),
    ("groupes ?search=zzzzzzzz", "/api/groupes", "/api/groupes?search=zzzzzzzz"),
    ("seances ?date_debut=2099-01-01", "/api/seances", "/api/seances?date_debut=2099-01-01"),
    ("seances ?statut=annulee", "/api/seances", "/api/seances?statut=annulee"),
    ("seances-groupe ?date=1900-01-01", "/api/seances-groupe", "/api/seances-groupe?date=1900-01-01"),
    ("calendrier ?date_fin=1900-01-01", "/api/calendrier", "/api/calendrier?date_fin=1900-01-01"),
    ("taches ?statut=fait", "/api/taches", "/api/taches?statut=fait"),
]
for libelle, sans, avec in comparaisons:
    _, a = get(sans)
    _, b = get(avec)
    na, nb = n_of(a), n_of(b)
    verifie(f"{libelle:34} {na} -> {nb}", isinstance(a, list) and isinstance(b, list) and nb < na)

# Filtres positifs : doivent retrouver la ligne creee
if seance_id and pid:
    _, f = get(f"/api/seances?patient_id={pid}")
    verifie("seances ?patient_id= retrouve la seance creee",
            isinstance(f, list) and any(x["id"] == seance_id for x in f))
    _, f = get("/api/seances?date=2031-03-04")
    verifie("seances ?date= retrouve la seance creee",
            isinstance(f, list) and any(x["id"] == seance_id for x in f))
if sg_id and gid:
    _, f = get(f"/api/seances-groupe?groupe_id={gid}")
    verifie("seances-groupe ?groupe_id= retrouve la seance creee",
            isinstance(f, list) and any(x["id"] == sg_id for x in f))
    code, membres = get(f"/api/groupes/{gid}/patients")
    if membres:
        mid = membres[0]["id"]
        _, f = get(f"/api/seances-groupe?patient_id={mid}")
        verifie("seances-groupe ?patient_id= (participant) retrouve la seance",
                isinstance(f, list) and any(x["id"] == sg_id for x in f))

# ─── 6. Notes patient : auteur + medias + date_creation ───────────────────────
print("\n--- 6. NOTES PATIENT (auteur imbrique + medias) ---")
if pid:
    r = c.post(f"/api/patients/{pid}/notes", headers=H,
               json={"contenu": "note smoke test", "medias": ["/uploads/x.jpg"]})
    verifie("POST note avec medias", r.status_code in (200, 201), str(r.status_code))
    if r.status_code in (200, 201):
        b = r.json()
        verifie("la note renvoie auteur imbrique (nom du redacteur)",
                isinstance(b.get("auteur"), dict) and b["auteur"].get("nom"),
                json.dumps(b.get("auteur"), ensure_ascii=False))
        verifie("la note renvoie medias + date_creation",
                b.get("medias") == ["/uploads/x.jpg"] and b.get("date_creation"),
                f"medias={b.get('medias')} date_creation={b.get('date_creation')}")
        code, notes = get(f"/api/patients/{pid}/notes")
        trouvee = next((x for x in notes if x["id"] == b["id"]), None) if isinstance(notes, list) else None
        verifie("auteur present aussi dans la LISTE des notes",
                isinstance(trouvee, dict) and isinstance(trouvee.get("auteur"), dict))
        verifie("DELETE de la note", c.delete(f"/api/notes/{b['id']}", headers=H).status_code == 204)

# ─── 7. Nettoyage ─────────────────────────────────────────────────────────────
print("\n--- 7. NETTOYAGE ---")
for path, libelle in a_nettoyer:
    r = c.delete(path, headers=H)
    verifie(f"suppression de la {libelle} temporaire", r.status_code == 204, str(r.status_code))

echecs = [libelle for ok, libelle in resultats if not ok]
print(f"\n===== {len(resultats) - len(echecs)}/{len(resultats)} verifications OK =====")
for libelle in echecs:
    print(f"  ECHEC -> {libelle}")
