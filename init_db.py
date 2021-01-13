"""This module is for creating the database of the flask applicaiton"""
import sqlite3
import os
import hashlib
import getpass


# Détermination d'un mot de passe admin au démarrage

ADM_PSW1 = "a"
ADM_PSW2 = "b"

while ADM_PSW1 != ADM_PSW2:
    ADM_PSW1 = getpass.getpass("Choisissez un mot de passe admin : ")
    ADM_PSW2 = getpass.getpass("Confirmez le mot de passe admin : ")
    if ADM_PSW1 != ADM_PSW2:
        print("Les mots de passe entrés sont différents. Veuillez réessayer.")

admin_password = ADM_PSW1

# Suppression des tables si existantes

conn = sqlite3.connect("profils_utilisateurs.db")
cur = conn.cursor()
cur.execute("DROP TABLE IF EXISTS utilisateurs")
cur.execute("DROP TABLE IF EXISTS appareils")
cur.execute("DROP TABLE IF EXISTS postes")
cur.execute("DROP TABLE IF EXISTS sites")
cur.execute("DROP TABLE IF EXISTS chaines")
cur.execute("DROP TABLE IF EXISTS lignes")
cur.execute("DROP TABLE IF EXISTS types_appareil")
cur.execute("DROP TABLE IF EXISTS niveau_resp")

# Création de la table utilisateurs si elle n'existe pas

cur.execute(
    """CREATE TABLE IF NOT EXISTS utilisateurs
            (identifiant TEXT PRIMARY KEY,
            hash_mdp TEXT,
            site TEXT,
            chaine_service TEXT,
            ligne_de_production TEXT,
            poste_tenu TEXT,
            FOREIGN KEY (site) REFERENCES sites(site),
            FOREIGN KEY (chaine_service) REFERENCES chaines(chaine),
            FOREIGN KEY (ligne_de_production) REFERENCES lignes(ligne),
            FOREIGN KEY (poste_tenu) REFERENCES postes(poste))"""
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
                ligne_de_production,
                poste_tenu) VALUES (?, ?, ?, ?, ?, ?)""",
        ("admin", hash_mdp, "direction_generale", "DSI", "", "directeur SI")
    )

salt = os.urandom(32)
key = hashlib.pbkdf2_hmac(
    "sha256", "0000".encode("utf-8"), salt, 100000, dklen=128
)
hash_mdp = salt + key

# Insertion de quelques utilisateurs

for user in [["alix", hash_mdp, "direction générale", "", "", "directeur général"],
        ["andrea", hash_mdp, "direction générale", "", "", "directeur des achats"],
        ["sacha", hash_mdp, "A", "", "", "responsable site"],
        ["alex", hash_mdp, "A", "", "", "responsable appro site"],
        ["charlie", hash_mdp, "A", "A1", "", "responsable chaine"],
        ["camille", hash_mdp, "A", "A1", "préparation", "pilote de ligne"]]:
    cur.execute(
        """INSERT INTO utilisateurs (
                identifiant,
                hash_mdp,
                site,
                chaine_service,
                ligne_de_production,
                poste_tenu)
        VALUES (?, ?, ?, ?, ?, ?)""",
        (user[0], user[1], user[2], user[3], user[4], user[5])
    )

# Création de la table appareils si elle n'existe pas

cur.execute(
    """CREATE TABLE IF NOT EXISTS appareils
            (appareil TEXT PRIMARY KEY,
            type TEXT,
            site_de_production TEXT,
            chaine_de_production TEXT,
            ligne_de_production TEXT,
            FOREIGN KEY (site_de_production) REFERENCES sites(site),
            FOREIGN KEY (chaine_de_production) REFERENCES chaines(chaine),
            FOREIGN KEY (ligne_de_production) REFERENCES lignes(ligne))"""
)

# Insertion d'appareils

for chaine in ["A1", "B1", "B2", "B3", "C1", "C2"]:
    for appareil in [[chaine + "_P1", "P1", chaine[0], chaine, "préparation"],
        [chaine + "_VM1", "VM1", chaine[0], chaine, "préparation"],
        [chaine + "_VT1", "VT1", chaine[0], chaine, "préparation"],
        [chaine + "_T1", "T1", chaine[0], chaine, "cuisson"],
        [chaine + "_VT2", "VT2", chaine[0], chaine, "cuisson"],
        [chaine + "_P2", "P2", chaine[0], chaine, "emballage"]]:
        cur.execute(
            """INSERT INTO appareils
            (appareil, type, site_de_production, chaine_de_production, ligne_de_production)
            VALUES (?, ?, ?, ?, ?)""",
            (appareil[0], appareil[1], appareil[2], appareil[3], appareil[4]),
            )

# Création de la table postes si elle n'existe pas

cur.execute(
    """CREATE TABLE IF NOT EXISTS postes
            (poste TEXT PRIMARY KEY,
            niveau_de_responsabilite TEXT,
            appareils_vus TEXT)"""
)

# Insertion de postes

for poste in [["directeur général", "direction générale", "TOUS"],
    ["directeur des achats", "direction générale", "P1"],
    ["responsable de site", "site", "TOUS"],
    ["responsable appro site", "site", "P1"],
    ["responsable de chaine", "chaine", "TOUS"],
    ["responsable de ligne", "ligne", "TOUS"]]:
    cur.execute(
        """INSERT INTO postes
            (poste, niveau_de_responsabilite, appareils_vus) VALUES (?, ?, ?)""",
            (poste[0], poste[1], poste[2]),
        )

# Création de la table sites si elle n'existe pas

cur.execute(
    """CREATE TABLE IF NOT EXISTS sites
            (site TEXT PRIMARY KEY)"""
)

# Insertion de sites

for site in ["direction générale", "A", "B", "C"]:
    cur.execute("""INSERT INTO sites (site) VALUES (?)""", (site,))

# Création de la table chaines si elle n'existe pas

cur.execute(
    """CREATE TABLE IF NOT EXISTS chaines
            (chaine TEXT PRIMARY KEY)"""
)

# Insertion de chaines

for chaine in ["A1", "B1", "B2", "B3", "C1", "C2"]:
    cur.execute("""INSERT INTO chaines (chaine) VALUES (?)""", (chaine,))

# Création de la table lignes si elle n'existe pas

cur.execute(
    """CREATE TABLE IF NOT EXISTS lignes
            (ligne TEXT PRIMARY KEY)"""
)

# Insertion de lignes

for ligne in ["préparation", "cuisson", "emballage"]:
    cur.execute("""INSERT INTO lignes (ligne) VALUES (?)""", (ligne,))

# Création de la table types_appareil si elle n'existe pas

cur.execute(
    """CREATE TABLE IF NOT EXISTS types_appareil
            (type_appareil TEXT PRIMARY KEY,
            description TEXT)"""
)

# Insertion de types d'appareil

for type_appareil in [["P1", "Poids cuve matière première"],
    ["VM1", "Vitesse malaxage"],
    ["VT1", "Vitesse tapis ligne préparation"],
    ["T1", "Température four"],
    ["VT2", "Vitesse tapis ligne cuisson"],
    ["P2", "Poids produit fini"]]:
    cur.execute("""INSERT INTO types_appareil
        (type_appareil, description) VALUES (?, ?)""",
        (type_appareil[0], type_appareil[1]))

# Création de la table niveau_resp si elle n'existe pas

cur.execute(
    """CREATE TABLE IF NOT EXISTS niveau_resp
            (niv_resp TEXT PRIMARY KEY)"""
)

# Insertion de types d'appareil

for niv_resp in ["direction générale","site", "chaine", "ligne"]:
    cur.execute("""INSERT INTO niveau_resp (niv_resp) VALUES (?)""", (niv_resp,))

cur.close()
conn.commit()
conn.close()
