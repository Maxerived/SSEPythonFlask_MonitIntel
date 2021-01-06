"""This module is for creating the database of the flask applicaiton"""
import sqlite3
import os
import hashlib
import getpass

ADM_PSW1 = "a"
ADM_PSW2 = "b"

while ADM_PSW1 != ADM_PSW2:
    ADM_PSW1 = getpass.getpass("Choisissez un mot de passe admin : ")
    ADM_PSW2 = getpass.getpass("Confirmez le mot de passe admin : ")
    if ADM_PSW1 != ADM_PSW2:
        print("Les mots de passe entrés sont différents. Veuillez réessayer.")

admin_password = ADM_PSW1

conn = sqlite3.connect("profils_utilisateurs.db")
cur = conn.cursor()
cur.execute("DROP TABLE IF EXISTS utilisateurs")
cur.execute("DROP TABLE IF EXISTS appareils")

# Création de la table utilisateurs si elle n'existe pas

cur.execute(
    """CREATE TABLE IF NOT EXISTS utilisateurs
            (identifiant TEXT PRIMARY KEY,
            hash_mdp TEXT,
            site TEXT,
            chaine_service TEXT,
            ligne_de_production TEXT,
            poste_tenu TEXT)"""
)

# Création du hash à insérer dans la base de données pour admin

salt = os.urandom(32)
key = hashlib.pbkdf2_hmac(
    "sha256", admin_password.encode("utf-8"), salt, 100000, dklen=128
)
hash_mdp = salt + key

# Insertion de l'utilisateur admin

cur.execute(
    """INSERT INTO utilisateurs
                (identifiant,
                hash_mdp,
                site,
                chaine_service,
                poste_tenu) VALUES (?, ?, ?, ?, ?)""",
        ("admin", hash_mdp, "direction_generale", "DSI", "directeur"),
    )

# Création de la table appareils si elle n'existe pas

cur.execute(
    """CREATE TABLE IF NOT EXISTS appareils
            (appareil TEXT PRIMARY KEY,
            type TEXT,
            site_de_production TEXT,
            chaine_de_production TEXT,
            ligne_de_production TEXT)"""
)

cur.close()
conn.commit()
conn.close()
