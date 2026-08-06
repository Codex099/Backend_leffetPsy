import sqlite3
import os

DB_PATH = "psycare.db"

def migrate():
    if not os.path.exists(DB_PATH):
        print(f"Base de données {DB_PATH} introuvable, pas de migration nécessaire.")
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Vérifier si la colonne 'sexe' existe déjà dans la table 'patients'
    cursor.execute("PRAGMA table_info(patients)")
    columns = [row[1] for row in cursor.fetchall()]

    if "sexe" not in columns:
        print("Ajout de la colonne 'sexe' à la table 'patients'...")
        cursor.execute("ALTER TABLE patients ADD COLUMN sexe VARCHAR")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_patients_sexe ON patients (sexe)")
        conn.commit()
        print("Migration de 'sexe' terminée avec succès.")
    else:
        print("La colonne 'sexe' existe déjà dans 'patients'.")

    conn.close()

if __name__ == "__main__":
    migrate()
