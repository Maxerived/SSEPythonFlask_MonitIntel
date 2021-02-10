"""Fichier principal"""

import hashlib
import json
import os
import queue
import secrets
import sqlite3
import time
from collections import deque
from datetime import datetime

from flask import (
    Flask,
    Response,
    escape,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from pubsub import pub

from getdata import *

app = Flask(__name__)

secret = secrets.token_urlsafe(32)
app.secret_key = secret


@app.route("/")
def index():

    if session.get("username") == "admin":
        return redirect(url_for("admin"))

    if session.get("username") is not None:
        # return """
        #     <link rel="icon" type="image/png" href="/static/img/favicon.ico"/>
        #     <button onclick="window.location.href='/graph';">Dashboard</button>
        #     <button onclick="window.location.href='/logout';">Logout</button>
        #     <p>Logged in as %s<p>
        # """ % escape(
        #     session["username"]
        # )
        session["appareils"] = get_seen_devices(session["username"])
        return render_template("dashboard.html", appareils=session["appareils"],username=session["username"])

    return redirect(url_for("login"))


@app.route("/admin")
def admin():

    if "username" in session:

        if session.get("username") == "admin":

            # Recupération des données à insérer dans les menus déroulants

            data = get_fields_data()
            postes = [""] + data[0]
            sites = data[1]
            # exception! Choix vide fait dans html, pour limiter les choix selon le poste choisi.
            chaines = data[2]
            # exception! Choix vide fait dans html, pour limiter les choix selon le site choisi.
            lignes = [""] + data[3]
            types = [""] + data[4]
            types_descr = [""] + data[5]
            nivs_resp = [""] + data[6]

            types_app = [""]
            for i in range(1, len(types)):
                types_app.append(types[i] + "_" + types_descr[i])

            return render_template(
                "admin.html",
                postes=postes,
                sites=sites,
                chaines=chaines,
                lignes=lignes,
                types=types_app,
                nivs_resp=nivs_resp,
                types_for_poste=types_app + ["TOUS"],
                error=session.get("error"),
            )

        return redirect(url_for("index"))

    return redirect(url_for("login"))


@app.route("/login", methods=["GET", "POST"])
def login():

    if "username" in session:

        if session["username"] == "admin":
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
            error = "[ERROR] Cet identifiant n'existe pas dans la base de données."
            return render_template("login.html", error=error)

        # Récupération du salt et calcul du hash avec le salt et le mdp entré apr l'utilisateur

        salt = hash_mdp[:32]
        key = hashlib.pbkdf2_hmac(
            "sha256", input_mdp.encode("utf-8"), salt, 100000, dklen=128
        )

        # Si le mot de passe est incorrect

        if hash_mdp[32:] != key:
            print("[ERROR] Mot de passe incorrect")
            error = "Le mot de passe est incorrect."
            return render_template("login.html", error=error)

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

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.pop("username", None)
    session.pop("appareils", None)
    session.pop("error", None)
    return redirect(url_for("login"))


@app.route("/admin/add_user", methods=["POST"])
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


@app.route("/admin/add_device", methods=["POST"])
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
def add_post_type():
    """Fonction pour ajouter un appareil dans la base de données"""

    # Récupération des valeurs entrées sur le formulaire

    post_form = request.form
    poste = post_form["poste"]
    niv_resp = post_form["niv_resp"]
    type_for_poste = post_form["type_for_poste"].split("_")[0]

    # Connexion à la base de données

    conn = sqlite3.connect("profils_utilisateurs.db")
    cur = conn.cursor()
    print("[INFO] Connexion réussie à SQLite")

    # Insertion d'un nouvel appareil dans la base de données

    try:
        cur.execute(
            """INSERT INTO postes
                    (poste,
                    niveau_de_responsabilite,
                    appareils_vus) VALUES (?, ?, ?)""",
            (poste, niv_resp, type_for_poste),
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


@app.route("/get_data")
def get_data():

    #    if session.get('username') == 'admin':
    #        return redirect(url_for('admin'))

    #    if session.get('username') is None:
    #        return redirect(url_for('login'))

    #    devices = get_seen_devices(session['username'])

    data = {}
    for app in ["A1_P1", "A1_P2", "A1_T1", "A1_VM1", "A1_VT1", "A1_VT2"]:
        data[app] = {}
        for i in range(len(X[app])):
            data[app][i + 1] = {}
            for j, K in [("x", X), ("y", Y), ("z", Z)]:
                data[app][i + 1][j] = K[app][i]

    return jsonify(data)


@app.route("/graph")
def graph():

    if session.get("username") is None:
        return redirect(url_for("login"))

    if session.get("username") == "admin":
        return redirect(url_for("admin"))
    
    session["appareils"] = get_seen_devices(session["username"])
    
    return render_template("graph.html", appareils=session["appareils"])


@app.route('/chart-data')
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
                time.sleep(1/acc_fact)

    return Response(generate_data(), mimetype="text/event-stream")



if __name__ == "__main__":
    app.run(debug=True, ssl_context=("cert.pem", "key.pem"))
