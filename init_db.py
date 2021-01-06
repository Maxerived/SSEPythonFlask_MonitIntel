"""This module is for creating the database of the flask applicaiton"""
import sqlite3
import os
import hashlib
import getpass

adm_psw1 = "a"
adm_psw2 = "b"

while adm_psw1 != adm_psw2:
    adm_psw1 = getpass.getpass("Choisissez un mot de passe admin : ")
    adm_psw2 = getpass.getpass("Confirmez le mot de passe admin : ")
    if adm_psw1 != adm_psw2:
        print("Les mots de passe entrés sont différents. Veuillez réessayer.")

admin_password = adm_psw1

conn = sqlite3.connect("profils_utilisateurs.db")
cur = conn.cursor()
cur.execute("DROP TABLE IF EXISTS utilisateurs")
cur.execute("DROP TABLE IF EXISTS appareils")

# Création de la table utilisateurs si elle n'existe pas

cur.execute(
    """CREATE TABLE IF NOT EXISTS utilisateurs
            (identifiant TEXT PRIMARY KEY,
            hash_mdp TEXT,
            entreprise TEXT,
            section_departement TEXT,
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
                (identifiant, hash_mdp, entreprise, section_departement, poste_tenu) VALUES (?, ?, ?, ?, ?)""",
        ("admin", hash_mdp, "Central", "DSI", "DSI"),
    )

# Création de la table appareils si elle n'existe pas

cur.execute(
    """CREATE TABLE IF NOT EXISTS appareils
            (entreprise TEXT,
            section_departement TEXT,
            appareil TEXT PRIMARY KEY,
            variable_mesuree TEXT)"""
)

cur.close()
conn.commit()
conn.close()
