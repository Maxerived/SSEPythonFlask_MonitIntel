"""This module is for creating the database of the flask applicaiton"""
import sqlite3

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

# Création de la table appareils si elle n'existe pas

cur.execute(
    """CREATE TABLE IF NOT EXISTS appareils
            (entreprise TEXT,
            section_departement TEXT,
            appareil TEXT PRIMARY KEY,
            variable_mesuree TEXT)"""
)

conn.commit()
conn.close()
