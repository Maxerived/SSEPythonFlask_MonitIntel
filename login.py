import hashlib
import os
import sqlite3
from functools import wraps
from flask import redirect, session, url_for

def admin_required(f):
    """Décorateur pour vérifier que l'utilisateur est bien authentifié comme admin"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
    
        if session.get('username') != 'admin':
            return redirect(url_for('login'))
    
        return f(*args, **kwargs)
    
    return decorated_function


def login_required(f):
    """Décorateur pour vérifier que l'utilisateur est bien authentifié"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
    
        if session.get('username') == 'admin':
            return redirect(url_for('admin'))
    
        if session.get('username') is None:
            return redirect(url_for('login'))
    
        return f(*args, **kwargs)
    
    return decorated_function


def hash(psw):
    """Fonction qui hashe un mot de passe"""

    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac(
        "sha256", psw.encode("utf-8"), salt, 100000, dklen=128
    )
    return salt + key


def get_hash_from_db(identifiant):

    # Connexion à la base de données

    conn = sqlite3.connect("profils_utilisateurs.db")
    cur = conn.cursor()
    print("[INFO] Connexion réussie à SQLite")

    # Récupération du hash_mdp à partir de l'identifiant

    cur.execute(
        "SELECT hash_mdp FROM utilisateurs WHERE identifiant = ?", (identifiant,)
    )
    res = cur.fetchall()

    # Fermeture de la base de données

    cur.close()
    conn.close()
    print("[INFO] Connexion SQlite fermée")

    if len(res) == 0:
        return None

    return res[0][0]


def check_credentials(identifiant, input_mdp):
    """Fonction qui vérifie les credentials entrés par l'utilisateur
    et renvoie un message pour orienter vers la suite à donner"""

    # Récupération du hash_mdp dans la base de données à partir de l'identifiant
    hash_mdp = get_hash_from_db(identifiant)
    print("[INFO] Hash récupéré")

    # Si l'identifiant n'est pas dans la base de données
    if hash_mdp == None:
        return "Cet identifiant n'existe pas dans la base de données."

    # Récupération du salt et calcul du hash avec le salt et le mdp entré apr l'utilisateur
    salt = hash_mdp[:32]
    key = hashlib.pbkdf2_hmac(
        "sha256", input_mdp.encode("utf-8"), salt, 100000, dklen=128
    )

    # Si le mot de passe est incorrect
    if hash_mdp[32:] != key:
        print("[ERROR] Mot de passe incorrect")
        return "Le mot de passe est incorrect."

    # Si l'identifiant et le mot de passe sont corrects,
    # instanciation de la session avec l'identifiant
    print("[INFO] Mot de passe correct")

    return "OK"


