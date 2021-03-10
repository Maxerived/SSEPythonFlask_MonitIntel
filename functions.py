import sqlite3
from login import *


def change_psw(identifiant, new_psw, new_psw2, current_psw=None):
    """Fonction qui permet à un utilisateur lambda de modifier
    son mot de passedans la base de données utilisateurs"""

    # Vérification du mot de passe actuel
    if current_psw is not None or identifiant is "admin":
        result = check_credentials(identifiant, current_psw)

    # Si le mot de pase actuel entré est correct
    if current_psw is None or result is "OK":
        
        # Si les deux nouveaux mots de passe sont différents
        if new_psw != new_psw2:
            result = "Les deux instances du nouveau mot de passe sont différentes."
        
        # Sinon, si les deux nouveaux mots de passe sont identiques
        else:
            hash_new_psw = hash(new_psw)

            try:
                # Connexion à la base de données
                conn = sqlite3.connect("profils_utilisateurs.db")
                cur = conn.cursor()
                print("[INFO] Connexion réussie à SQLite")

                # Insertion d'un nouvel utilisateur dans la base de données
                cur.execute(
                    """UPDATE utilisateurs SET hash_mdp = ? WHERE identifiant = ?""",
                    (hash_new_psw, identifiant)
                )

                print("[INFO] Mot de passe modifié avec succès")
                result = "Le mot de passe a été modifié avec succès"

            except:
                result = "Une erreur est survenue lors du changement du mot de passe"

            finally:
                cur.close()
                conn.commit()
                conn.close()
                print("[INFO] Connexion SQlite fermée")

    return result


def new_user(identifiant, mdp, site, chaine, ligne, poste):
    """Fonction qui permet d'insérer un nouvel utilisateur dans le base données utilisateurs"""

    # Création du hash du mot de passe et du salt associé
    hash_mdp = hash(mdp)

    # Insertion d'un nouvel utilisateur dans la base de données
    try:
        # Connexion à la base de données
        conn = sqlite3.connect("profils_utilisateurs.db")
        cur = conn.cursor()
        print("[INFO] Connexion réussie à SQLite")
    
        cur.execute(
            """INSERT INTO utilisateurs
                    (identifiant,
                    hash_mdp,
                    site,
                    chaine_service,
                    ligne_de_production,
                    poste_tenu) VALUES (?, ?, ?, ?, ?, ?)""",
            (identifiant, hash_mdp, site, chaine, ligne, poste),
        )
        result = "Nouvel utilisateur intégré dans la base de données"
        print("[INFO] Utilisateur intégré dans la base de données avec succès")

    except sqlite3.IntegrityError:
        result = "Cet identifiant existe déjà dans la base de données !!!"
        print(
            "[ERROR] Échec lors de l'insertion d'un nouvel utilisateur : identifiant déjà existant"
        )

    # Fermeture de la base de données
    finally:
        cur.close()
        conn.commit()
        conn.close()
        print("[INFO] Connexion SQlite fermée")

    return result


def del_user(identifiant):
    """Fonction qui supprime un utilisateur de la base de données utilisateurs"""

    try:
        # Connexion à la base de données
        conn = sqlite3.connect("profils_utilisateurs.db")
        cur = conn.cursor()
        print("[INFO] Connexion réussie à SQLite")

        # Suppresion de l'utilisateur de la base de données
        cur.execute("""DELETE FROM utilisateurs WHERE identifiant = ?""", (identifiant,))
        result = "Utilisateur {} supprimé de la base de données".format(identifiant)
        print("[INFO] {} avec succès".format(result))

    except:
        result = "Impossible de supprimer l'utilisateur " + identifiant
        print("[ERROR] Échec lors de la suppression de l'utilisateur")

    # Fermeture de la base de données
    finally:
        cur.close()
        conn.commit()
        conn.close()
        print("[INFO] Connexion SQlite fermée")

    return result


def new_device(appareil, type_app, site, chaine, ligne):
    """Fonction qui ajoute un appareil à la base de données"""

    try:
        # Connexion à la base de données
        conn = sqlite3.connect("profils_utilisateurs.db")
        cur = conn.cursor()
        print("[INFO] Connexion réussie à SQLite")

        # Insertion d'un nouvel appareil dans la base de données
        cur.execute(
            """INSERT INTO appareils
                    (appareil,
                    type,
                    site_de_production,
                    chaine_de_production,
                    ligne_de_production) VALUES (?, ?, ?, ?, ?)""",
            (appareil, type_app, site, chaine, ligne),
        )
        result = "Nouvel appareil intégré dans la base de données"
        print("[INFO] Appareil intégré dans la base de données avec succès")

    except sqlite3.IntegrityError:
        result = "Cet appareil existe déjà dans la base de données !!!"
        print(
            "[ERROR] Échec lors de l'insertion d'un nouvel appareil : identifiant déjà existant"
        )

    # Fermeture de la base de données
    finally:
        cur.close()
        conn.commit()
        conn.close()
        print("[INFO] Connexion SQlite fermée")

    return result


def new_post_type(poste, niv_resp, type_for_poste):
    """Fonction qui ajoute un nouveau type d'appareil"""

    try:
        # Connexion à la base de données
        conn = sqlite3.connect("profils_utilisateurs.db")
        cur = conn.cursor()
        print("[INFO] Connexion réussie à SQLite")

        # Insertion d'un nouvel appareil dans la base de données
        for type_app in type_for_poste:
            type_app = type_app.split('_', 1)[0]
            cur.execute(
                """INSERT INTO postes
                        (poste,
                        niveau_de_responsabilite,
                        appareils_vus) VALUES (?, ?, ?)""",
                (poste, niv_resp, type_app),
            )
        result = "Nouveau type de poste intégré dans la base de données"
        print("[INFO] Type de poste intégré dans la base de données avec succès")

    except sqlite3.IntegrityError:
        result = "Ce type de poste existe déjà dans la base de données !!!"
        print(
            "[ERROR] Échec lors de l'insertion d'un nouveau type de poste : identifiant déjà existant"
        )

    # Fermeture de la base de données
    finally:
        cur.close()
        conn.commit()
        conn.close()
        print("Connexion SQlite fermée")

    return result






