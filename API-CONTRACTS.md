# API Contracts — PsyCare Backend

> Ce document liste les schémas de requête et de réponse **exacts** pour les routes les plus sensibles.
> Son rôle est de permettre à l'agent mobile (Flutter/Dart) d'aligner ses payloads sans essais-erreurs.
> **Toute modification de schéma doit être répercutée ici.**

---

## Authentification

### POST /api/auth/login

**Request**
```json
{
  "username": "jean.dupont",
  "password": "MonMotDePasse123"
}
```

**Response 200**
```json
{
  "access_token": "<JWT>",
  "token_type": "bearer"
}
```

**Erreurs**
| Code | Cas |
|------|-----|
| 401 | Identifiants invalides |

---

## Employés — `POST /api/employees`

> ⚠️ Réservé aux admins (JWT avec `role=admin` requis).

**Request** *(tous les champs ci-dessous)*
```json
{
  "nom": "Dupont",
  "prenom": "Jean",
  "telephone": "+33612345678",
  "username": "jean.dupont",
  "password": "SecurePassword123",
  "role": "psychologue"
}
```

**Champs**
| Champ | Type | Requis | Notes |
|-------|------|--------|-------|
| `nom` | string | ✅ | — |
| `prenom` | string | ✅ | — |
| `telephone` | string | ✅ | Espaces en début/fin tolérés (strippés automatiquement) |
| `username` | string | ✅ | Doit être unique |
| `password` | string | ✅ | Envoyé en clair, haché côté backend (bcrypt). Jamais renvoyé ni loggé |
| `role` | enum | ✅ | Valeurs : `admin`, `psychologue`, `educatrice` (casse ignorée) |

**Response 201**
```json
{
  "id": "uuid",
  "nom": "Dupont",
  "prenom": "Jean",
  "telephone": "+33612345678",
  "username": "jean.dupont",
  "role": "psychologue"
}
```
> Le champ `password_hash` n'est **jamais** présent dans la réponse.

**Erreurs**
| Code | Cas |
|------|-----|
| 409 | `username` ou `telephone` déjà utilisé par un autre employé |
| 422 | Champ manquant ou valeur invalide (réponse champ-par-champ) |

---

## Calendrier — `POST /api/calendrier`

**Request**
```json
{
  "titre": "Réunion d'équipe",
  "date": "2026-08-15",
  "description": "Bilan mensuel",
  "notifier_avant_jours": 2
}
```

**Champs**
| Champ | Type | Requis | Notes |
|-------|------|--------|-------|
| `titre` | string | ✅ | — |
| `date` | date | ✅ | Formats acceptés : `YYYY-MM-DD` **ou** `YYYY-MM-DDTHH:MM:SS[Z]` (Flutter envoie parfois le second) |
| `description` | string | ❌ | nullable |
| `notifier_avant_jours` | int | ❌ | nullable, nombre de jours avant la date |

**Response 201**
```json
{
  "id": "uuid",
  "titre": "Réunion d'équipe",
  "date": "2026-08-15",
  "description": "Bilan mensuel",
  "notifier_avant_jours": 2,
  "cree_par": "uuid-employee"
}
```

**Erreurs**
| Code | Cas |
|------|-----|
| 422 | `date` absente ou format non parsable (ex: `"15/08/2026"`) |

---

## Parents — `POST /api/parents`

**Request**
```json
{
  "nom": "Martin",
  "prenom": "Sophie",
  "telephone": "+33698765432",
  "etat_civil": "marie",
  "adresse": "12 rue de la Paix, Paris"
}
```

**Champs**
| Champ | Type | Requis | Notes |
|-------|------|--------|-------|
| `nom` | string | ✅ | — |
| `prenom` | string | ✅ | — |
| `telephone` | string | ✅ | **Doit être unique** — doublon → 409 Conflict |
| `etat_civil` | enum | ✅ | Valeurs : `marie`, `divorce`, `autre` |
| `adresse` | string | ❌ | nullable |

**Erreurs**
| Code | Cas |
|------|-----|
| 409 | Numéro de téléphone déjà utilisé par un autre parent |

---

## Rôles Parent (enum `patient_parents.role`)

> Utilisé dans `POST /api/patients/{id}/parents` → champ `role`

**Valeurs acceptées (US-M17 — étendues)**
```
pere | mere | grand_pere | grand_mere | oncle | tante | tuteur | autre
```

**Request exemple**
```json
{
  "parent_id": "uuid-parent",
  "role": "grand_mere"
}
```

---

## Groupes — Employés responsables

### GET `/api/groupes/{groupe_id}/employes`

**Response 200**
```json
[
  { "groupe_id": "uuid-groupe", "employe_id": "uuid-emp-1" },
  { "groupe_id": "uuid-groupe", "employe_id": "uuid-emp-2" }
]
```

---

### POST `/api/groupes/{groupe_id}/employes`

**Request** *(associer un employé)*
```json
{
  "employe_id": "uuid-employee"
}
```

**Comportement automatique :** l'employé reçoit l'accès à **tous les patients** membres du groupe dans `employee_patient_access` (idempotent).

**Response 201**
```json
{
  "groupe_id": "uuid-groupe",
  "employe_id": "uuid-employee"
}
```

**Erreurs**
| Code | Cas |
|------|-----|
| 409 | Employé déjà associé au groupe |

---

### POST `/api/groupes/{groupe_id}/employes/bulk`

**Request** *(associer plusieurs employés d'un coup)*
```json
{
  "employe_ids": ["uuid-emp-1", "uuid-emp-2", "uuid-emp-3"]
}
```

**Response 201**
```json
{
  "message": "2 employé(s) ajouté(s) au groupe."
}
```
> Les doublons (déjà associés) sont silencieusement ignorés — opération idempotente.

---

### DELETE `/api/groupes/{groupe_id}/employes/{employe_id}`

**Response 204** *(no content)*

**Erreurs**
| Code | Cas |
|------|-----|
| 404 | Employé non associé au groupe |

---

## Pagination — Paramètres communs

Les routes de listage suivantes supportent `?limit=` et `?offset=` :

| Route | Défaut limit | Notes |
|-------|-------------|-------|
| `GET /api/patients` | 100 | Combine avec `?actif=true/false` |
| `GET /api/employees` | 100 | Admin uniquement |
| `GET /api/parents` | 100 | — |
| `GET /api/groupes` | 100 | — |
| `GET /api/seances` | 100 | Triées par date DESC |
| `GET /api/seances-groupe` | 100 | Triées par date DESC |
| `GET /api/taches` | 100 | Filtrées par assigné si non-admin |

**Exemple**
```
GET /api/patients?limit=20&offset=40&actif=true
```

---

## Format standard des erreurs 4xx

Toutes les erreurs retournées par le backend respectent le format natif FastAPI/Pydantic :

**Erreur de validation (422)**
```json
{
  "detail": [
    {
      "loc": ["body", "date"],
      "msg": "Format de date invalide '15/08/2026' — format attendu : YYYY-MM-DD (ou YYYY-MM-DDTHH:MM:SS)",
      "type": "value_error"
    }
  ]
}
```

**Erreur métier (409, 404, 403…)**
```json
{
  "detail": "Un parent avec ce numéro de téléphone existe déjà."
}
```

> ⚠️ Aucun handler global ne masque ces erreurs — le détail est toujours accessible au client mobile.
