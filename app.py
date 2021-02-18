"""Fichier principal"""

import hashlib
import json
import os
import requests
import secrets
import sqlite3
import time
from contextlib import closing
from functools import wraps
from getdata import *

from flask import (
    Flask,
    redirect,
    render_template,
    request,
    Response,
    session,
    url_for,
)


app = Flask(__name__)

secret = secrets.token_urlsafe(32)
app.secret_key = secret


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


def templated(template=None):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            template_name = template
            if template_name is None:
                template_name = request.endpoint \
                    .replace('.', '/') + '.html'
            ctx = f(*args, **kwargs)
            if ctx is None:
                ctx = {}
            elif not isinstance(ctx, dict):
                return ctx
            return render_template(template_name, **ctx)
        return decorated_function
    return decorator


@app.route("/login", methods=["GET", "POST"])
@templated()
def login():

    if session.get('username') is not None:

        if session.get('username') == "admin":
            return redirect(url_for("admin"))

        return redirect(url_for("index"))

    if request.method == "POST":

        # Récupération des valeurs entrées sur le formlaire

        auth_form = request.form
        identifiant = auth_form["uname"]
        input_mdp = auth_form["psw"]

        # Récupération du hash_mdp dans la base de données à partir de l'identifiant

        hash_mdp = get_hash_from_db(identifiant)
        print("[INFO] Hash récupéré")

        # Si l'identifiant n'est pas dans la base de données

        if hash_mdp == None:
            error = "Cet identifiant n'existe pas dans la base de données."
            return dict(error=error)

        # Récupération du salt et calcul du hash avec le salt et le mdp entré apr l'utilisateur

        salt = hash_mdp[:32]
        key = hashlib.pbkdf2_hmac(
            "sha256", input_mdp.encode("utf-8"), salt, 100000, dklen=128
        )

        # Si le mot de passe est incorrect

        if hash_mdp[32:] != key:
            print("[ERROR] Mot de passe incorrect")
            error = "Le mot de passe est incorrect."
            return dict(error=error)

        # Si l'identifiant et le mot de passe sont corrects,
        # instanciation de la session avec l'identifiant

        print("[INFO] Mot de passe correct")
        error = "Vous êtes authentifié."
        session["username"] = identifiant

        # Si l'utilisateur est admin

        if identifiant == "admin":
            return redirect(url_for("admin"))

        # Pour un utilisateur lambda

        return redirect(url_for("index"))

    return {}


@app.route("/logout")
def logout():

    session.pop("username", None)
    session.pop("appareils", None)
    session.pop("error", None)
    
    return redirect(url_for("login"))


@app.route("/", methods=["GET"])
@login_required
@templated("dashboard.html")
def index():

    session["appareils"] = get_seen_devices(session["username"])

    return dict(appareils=session["appareils"], username=session["username"])


@app.route("/change_password", methods=["POST"])
@login_required
@templated("dashboard.html")
def change_password():

    if request.method == "POST":

        # Récupération des valeurs entrées sur le formlaire

        input_psw = request.form['input_psw']
        new_psw = request.form['new_psw']
        new_psw2 = request.form['new_psw2']

        if new_psw != new_psw2:
            error = "Les deux instances du nouveau mot de passe sont différentes."
            return dict(appareils=session["appareils"],
                        username=session["username"],
                        error=error)

        # Récupération du hash_mdp dans la base de données
        # à partir de l'identifiant

        hash_actual_psw = get_hash_from_db(session.get('username'))
        print("[INFO] Hash récupéré")

        # Si l'identifiant n'est pas dans la base de données

        if hash_actual_psw == None:
            error = "Cet identifiant n'existe pas dans la base de données."
            return dict(appareils=session["appareils"],
                        username=session["username"],
                        error=error)

        # Récupération du salt et calcul du hash avec le salt
        # et le mot de passe actuel entré par l'utilisateur

        salt = hash_actual_psw[:32]
        key = hashlib.pbkdf2_hmac(
            "sha256", input_psw.encode("utf-8"), salt, 100000, dklen=128
        )

        # Si le mot de passe est incorrect

        if hash_actual_psw[32:] != key:
            print("[ERROR] Mot de passe incorrect")
            error = "Le mot de passe est incorrect."
            return dict(appareils=session["appareils"],
                        username=session["username"],
                        error=error)

        # Si le mot de passe est correct et que les deux instances
        # du nouveau mot de passe sont les mêmes

        salt = os.urandom(32)
        key = hashlib.pbkdf2_hmac(
            "sha256", new_psw.encode("utf-8"), salt, 100000, dklen=128
        )
        hash_new_psw = salt + key

        # Connexion à la base de données

        conn = sqlite3.connect("profils_utilisateurs.db")
        cur = conn.cursor()
        print("[INFO] Connexion réussie à SQLite")

        # Insertion d'un nouvel utilisateur dans la base de données

        cur.execute(
            """UPDATE utilisateurs SET hash_mdp = ? WHERE identifiant = ?""",
            (hash_new_psw, session.get('username'))
        )
        error = "Le mot de passe a été modifié avec succès"
        print("[INFO] Mot de passe modifié avec succès")

        cur.close()
        conn.commit()
        conn.close()
        print("[INFO] Connexion SQlite fermée")

    return dict(appareils=session["appareils"],
                username=session["username"],
                error=error)


@app.route("/admin", methods=["GET"])
@admin_required
@templated('admin.html')
def admin():

    # Recupération des données à insérer dans les menus déroulants

    data = get_fields_data()
    postes = [""] + data[0]
    sites = data[1]
    # exception ! Choix vide fait dans html, pour limiter les choix selon le poste choisi.
    chaines = data[2]
    # exception ! Choix vide fait dans html, pour limiter les choix selon le site choisi.
    lignes = [""] + data[3]
    types = [""] + data[4]
    types_descr = [""] + data[5]
    nivs_resp = [""] + data[6]
    utilisateurs = data[7][1:] # Suppression de l'admin dans les choix possibles
    
    types_app = [""]
    for i in range(1, len(types)):
        types_app.append(types[i] + "_" + types_descr[i])

    return dict(postes=postes,
                sites=sites,
                chaines=chaines,
                lignes=lignes,
                types=types_app,
                nivs_resp=nivs_resp,
                types_for_poste=types_app + ["TOUS"],
                utilisateurs=utilisateurs,
                error=session.get("error"))


@app.route("/admin/add_user", methods=["POST"])
@admin_required
def add_user():
    """Fonction pour ajouter un utilisateur dans la base de données"""

    # Récupération des valeurs entrées sur le formulaire

    user_form = request.form
    identifiant = user_form["uname"]
    site = user_form["site"]
    chaine = user_form["chaine"]
    ligne = user_form["ligne"]
    poste = user_form["poste"]

    # Création du hash du mot de passe et du salt associé

    salt = os.urandom(32)
    key = hashlib.pbkdf2_hmac(
        "sha256", user_form["psw"].encode("utf-8"), salt, 100000, dklen=128
    )
    hash_mdp = salt + key

    # Connexion à la base de données

    conn = sqlite3.connect("profils_utilisateurs.db")
    cur = conn.cursor()
    print("[INFO] Connexion réussie à SQLite")

    # Insertion d'un nouvel utilisateur dans la base de données

    try:
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
        error = "Nouvel utilisateur intégré dans la base de données"
        print("[INFO] Utilisateur intégré dans la base de données avec succès")

    except sqlite3.IntegrityError:
        error = "Cet identifiant existe déjà dans la base de données !!!"
        print(
            "[ERROR] Échec lors de l'insertion d'un nouvel utilisateur : identifiant déjà existant"
        )

    # Fermeture de la base de données
    finally:
        cur.close()
        conn.commit()
        conn.close()
        print("[INFO] Connexion SQlite fermée")

    session["error"] = error

    return redirect(url_for("admin"))


@app.route("/admin/delete_user", methods=["POST"])
@admin_required
def delete_user():
    """Fonction pour supprimer un utilisateur de la base de données"""

    # Récupération de l'utilisateur à supprimer

    user_form = request.form
    identifiant = user_form["uname"]

    # Connexion à la base de données

    conn = sqlite3.connect("profils_utilisateurs.db")
    cur = conn.cursor()
    print("[INFO] Connexion réussie à SQLite")

    # Insertion d'un nouvel utilisateur dans la base de données

    try:
        cur.execute("""DELETE FROM utilisateurs WHERE identifiant = ?""", (identifiant,))
        error = "Utilisateur {} supprimé de la base de données".format(identifiant)
        print("[INFO] {} avec succès".format(error))

    except:
        error = "Impossible de supprimer l'utilisateur " + identifiant
        print("[ERROR] Échec lors de la suppression de l'utilisateur")

    # Fermeture de la base de données

    finally:
        cur.close()
        conn.commit()
        conn.close()
        print("[INFO] Connexion SQlite fermée")

    session["error"] = error

    return redirect(url_for("admin"))


@app.route("/admin/add_device", methods=["POST"])
@admin_required
def add_device():
    """Fonction pour ajouter un appareil dans la base de données"""

    # Récupération des valeurs entrées sur le formulaire

    device_form = request.form
    appareil = device_form["appareil"]
    type_app = device_form["type"].split("_")[0]
    site = device_form["site"]
    chaine = device_form["chaine"]
    ligne = device_form["ligne"]

    # Connexion à la base de données

    conn = sqlite3.connect("profils_utilisateurs.db")
    cur = conn.cursor()
    print("[INFO] Connexion réussie à SQLite")

    # Insertion d'un nouvel appareil dans la base de données

    try:
        cur.execute(
            """INSERT INTO appareils
                    (appareil,
                    type,
                    site_de_production,
                    chaine_de_production,
                    ligne_de_production) VALUES (?, ?, ?, ?, ?)""",
            (appareil, type_app, site, chaine, ligne),
        )
        error = "Nouvel appareil intégré dans la base de données"
        print("[INFO] Appareil intégré dans la base de données avec succès")

    except sqlite3.IntegrityError:
        error = "Cet appareil existe déjà dans la base de données !!!"
        print(
            "[ERROR] Échec lors de l'insertion d'un nouvel appareil : identifiant déjà existant"
        )

    # Fermeture de la base de données
    finally:
        cur.close()
        conn.commit()
        conn.close()
        print("[INFO] Connexion SQlite fermée")

    session["error"] = error

    return redirect(url_for("admin"))


@app.route("/admin/add_post_type", methods=["POST"])
@admin_required
def add_post_type():
    """Fonction pour ajouter un appareil dans la base de données"""

    # Récupération des valeurs entrées sur le formulaire

    post_form = request.form
    poste = post_form["poste"]
    niv_resp = post_form["niv_resp"]
    type_for_poste = [post_form["type_for_poste"].split("_")[0]]

    # Connexion à la base de données

    conn = sqlite3.connect("profils_utilisateurs.db")
    cur = conn.cursor()
    print("[INFO] Connexion réussie à SQLite")

    # Insertion d'un nouvel appareil dans la base de données

    try:
        for type_app in type_for_poste:
            cur.execute(
                """INSERT INTO postes
                        (poste,
                        niveau_de_responsabilite,
                        appareils_vus) VALUES (?, ?, ?)""",
                (poste, niv_resp, type_app),
            )
        error = "Nouveau type de poste intégré dans la base de données"
        print("[INFO] Type de poste intégré dans la base de données avec succès")

    except sqlite3.IntegrityError:
        error = "Ce type de poste existe déjà dans la base de données !!!"
        print(
            "[ERROR] Échec lors de l'insertion d'un nouveau type de poste : identifiant déjà existant"
        )

    # Fermeture de la base de données
    finally:
        cur.close()
        conn.commit()
        conn.close()
        print("Connexion SQlite fermée")

    session["error"] = error

    return redirect(url_for("admin"))


@app.route('/chart-data')
@login_required
def chart_data():

    appareils = session["appareils"]
    
    def generate_data():

        app_times = {}
        for app in appareils:
            app_times[app] = 0
        iter = 0
        nb_values = max([len(X[appareil]) for appareil in appareils])
        
        while True:
        
            if iter < nb_values:

                data = {}

                for appareil in appareils:

                    i = nb_values - len(X[appareil]) - iter + 1

                    if i > 0:
                        data[appareil] = {
                            'time': "",
                            'value' : "",
                            'anomaly' : 'null'
                        }

                    else:
                        data[appareil] = {
                            'time': str(X[appareil][-i]),
                            'value' : Y[appareil][-i],
                            'anomaly' : Z[appareil][-i]
                        }

                iter += 1
                json_data = json.dumps(data)
                yield f"data:{json_data}\n\n"
                time.sleep(1 / (2 * quelen * acc_fact))

            else:

                data = {}

                for appareil in appareils:

                    if len(X[appareil]) > 1 and X[appareil][-1] != app_times[appareil]:
                        data[appareil] = {
                            'time': str(X[appareil][-1]),
                            'value' : Y[appareil][-1],
                            'anomaly' : Z[appareil][-1]
                        }
                        app_times[appareil] = X[appareil][-1]

                    else:

                        data[appareil] = {
                            'time': "",
                            'value' : "",
                            'anomaly' : 'null'
                        }

                json_data = json.dumps(data)
                yield f"data:{json_data}\n\n"
                time.sleep(1 / acc_fact)

    return Response(generate_data(), mimetype="text/event-stream")

"""
@app.route('/device_data')
def send_device_data():

    def generate_device_data():

        yield '{"hello" : "world"}'
        time.sleep(0.1)

    return Response(generate_device_data(), mimetype="type/event-stream")


@app.route('/get_data')
def get_data():

    r = requests.get(request.host_url + url_for('send_device_data'), stream=True)
    while r.raw:
        print(r.raw.read())
        time.sleep(
    pass
"""

if __name__ == "__main__":
    app.run(debug=True, ssl_context=("cert.pem", "key.pem"))
