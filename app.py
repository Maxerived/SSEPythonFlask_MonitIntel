"""Fichier principal"""

import hashlib
import json
import os
import queue
import random
import secrets
import sqlite3
import time
import webbrowser as wb
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
        return """
            <link rel="icon" type="image/png" href="/static/img/favicon.ico"/>
            <button onclick="window.location.href='/logout';">Logout</button>
            <p>Logged in as %s<p>
        """ % escape(
            session["username"]
        )

    return redirect(url_for("login"))


@app.route("/admin")
def admin():

    if "username" in session:

        if session.get("username") == "admin":

            # Recupération des données à insérer dans les menus déroulants

            data = get_fields_data()
            postes = [""] + data[0]
            sites = [""] + data[1]
            chaines = [""] + data[2]
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
        print("Hash récupéré")

        # Si l'identifiant n'est pas dans la base de données

        if hash_mdp == None:
            error = "Cet identifiant n'existe pas dans la base de données."
            return render_template("login.html", error=error)

        # Récupération du salt et calcul du hash avec le salt et le mdp entré apr l'utilisateur

        salt = hash_mdp[:32]
        key = hashlib.pbkdf2_hmac(
            "sha256", input_mdp.encode("utf-8"), salt, 100000, dklen=128
        )

        # Si le mot de passe est incorrect

        if hash_mdp[32:] != key:
            print("Mot de passe incorrect")
            error = "Le mot de passe est incorrect."
            return render_template("login.html", error=error)

        # Si l'identifiant et le mot de passe sont corrects

        print("Mot de passe correct")
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
    print("Connexion réussie à SQLite")

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
        print("Utilisateur intégré dans la base de données avec succès")

    except sqlite3.IntegrityError:
        error = "Cet identifiant existe déjà dans la base de données !!!"
        print(
            "Échec lors de l'insertion d'un nouvel utilisateur : identifiant déjà existant"
        )

    # Fermeture de la base de données
    finally:
        cur.close()
        conn.commit()
        conn.close()
        print("Connexion SQlite fermée")

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
    print("Connexion réussie à SQLite")

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
        print("Appareil intégré dans la base de données avec succès")

    except sqlite3.IntegrityError:
        error = "Cet appareil existe déjà dans la base de données !!!"
        print(
            "Échec lors de l'insertion d'un nouvel appareil : identifiant déjà existant"
        )

    # Fermeture de la base de données
    finally:
        cur.close()
        conn.commit()
        conn.close()
        print("Connexion SQlite fermée")

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
    print("Connexion réussie à SQLite")

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
        print("Type de poste intégré dans la base de données avec succès")

    except sqlite3.IntegrityError:
        error = "Ce type de poste existe déjà dans la base de données !!!"
        print(
            "Échec lors de l'insertion d'un nouveau type de poste : identifiant déjà existant"
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
    return render_template("graph.html")


@app.route("/chart-data")
def chart_data():
    def generate_random_data():
        while True:
            json_data = json.dumps({"time": X["A1_P1"][0], "value": Y["A1_P1"][0]})
            yield f"data:{json_data}\n\n"
            time.sleep(1)

    return Response(generate_random_data(), mimetype="text/event-stream")


#############################################################################################@
#############################################################################################@


class MessageAnnouncer:
    def __init__(self):
        self.listeners = []

    def listen(self):
        q = queue.Queue(maxsize=5)
        self.listeners.append(q)
        return q

    def announce(self, msg):
        for i in reversed(range(len(self.listeners))):
            try:
                self.listeners[i].put_nowait(msg)
            except queue.Full:
                del self.listeners[i]


announcer = MessageAnnouncer()

# event: Jackson 5\\ndata: {"abc": 123}\\n\\n


def format_sse(data: str, event=None) -> str:
    msg = f"data: {data}\n\n"
    if event is not None:
        msg = f"event: {event}\n{msg}"
    return msg


@app.route("/input_data/<input_data>", methods=["GET"])
def get_values(input_data):
    input_data = str(input_data)
    input_var_elem = input_data.rsplit(".", 1)
    #    var = input_var_elem[0]
    if len(input_var_elem) > 1:
        extension = input_data.rsplit(".", 1)[1].lower()
        if extension not in {"csv", "tsv"}:
            return {"La ressource n'est pas au bon format"}, 200
        filename = input_data
        with open(filename, "r") as file:
            lines = file.readlines()
            if len(lines) <= 2:
                data = lines[1].split()[2]
            header = lines[0]
            #            mesured_var = header.split()[1]
            #             			print(mesured_var)
            filehead_time = datetime.strptime(
                " ".join(lines[1].split()[:2]), "%d/%m/%Y %H:%M:%S"
            )
            filetail_time = datetime.strptime(
                " ".join(lines[-1].split()[:2]), "%d/%m/%Y %H:%M:%S"
            )
            if filetail_time < filehead_time:
                data = lines[-1].split()[2]
                lines = lines[:-1]
            elif filetail_time > filehead_time:
                data = lines[1].split()[2]
                lines = [header] + lines[2:]
        file = open(filename, "w")
        file.write("".join(lines)[:-1])
        file.close()
        msg = format_sse(data=data)
        announcer.announce(msg=msg)
    return jsonify({"Status": "On progress..."}), 200


@app.route("/listen", methods=["GET"])
def listen():
    def stream():
        messages = announcer.listen()  # returns a queue.Queue
        while True:
            msg = messages.get()  # blocks until a new message arrives
            yield msg

    return Response(stream(), mimetype="text/event-stream")


#############################################################################################@
#############################################################################################@


# dates = matplotlib.dates.date2num(list_of_datetimes)
# matplotlib.pyplot.plot_date(dates, values)


if __name__ == "__main__":
    app.run(debug=True, ssl_context=("cert.pem", "key.pem"))
