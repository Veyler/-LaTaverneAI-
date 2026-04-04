import sqlite3
import os
from core.config import DB_PATH

db_path = DB_PATH
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    try:
        conn.execute("ALTER TABLE messages ADD COLUMN image_data TEXT;")
        conn.commit()
        print("Migration réussie : colonne image_data ajoutée.")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("Migration déjà effectuée.")
        else:
            print(f"Erreur : {e}")
    finally:
        conn.close()
else:
    print("Base de données introuvable.")
