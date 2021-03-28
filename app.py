"""Fichier principal"""

import json
import secrets
import time
from functools import wraps
from functions import *
from getdata import *
from login import *

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


def templated(template=None):
    """Décorateur qui permet d'appeler un template
    en fonction de la page requêtée"""
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
    """Fonction qui permet l'appel du template pour l'affichage
    de la page de connexion à l'API, la récupération des credentials
    entrés par l'utilisateur et l'authntification de ce dernier"""

    # Si quelqu'un est déjà logué
    if session.get('username') is not None:
        # S'il s'agit de l'administrateur
        if session.get('username') == "admin":
            # Renvoi vers la page admin
            return redirect(url_for("admin"))

        # Sinon, renvoi vers la page dashboard de l'utilisateur lambda
        return redirect(url_for("index"))

    # Si la méthode de requête est POST
    if request.method == "POST":

        # Vérification des credentials entrés par l'utilisateur
        result = check_credentials(
            request.form["uname"],
            request.form["psw"]
        )

        # Si les credentials sont incorrects
        if result is not "OK":
            return dict(error=result)

        # si les credentials sont corrects, instanciation de session
        session["username"] = request.form["uname"]

        # Si l'utilisateur est admin
        if request.form["uname"] == "admin":
            # Renvoi vers la page admin
            return redirect(url_for("admin"))

        # Pour un utilisateur lambda, renvoi vers la page dashboard
        return redirect(url_for("index"))


@app.route("/logout")
def logout():
    """Fonction premet de déloguer l'utilisateur
    et de supprimer les données de session"""

    # Suppression des données de session
    session.pop("username", None)
    session.pop("appareils", None)
    session.pop("error", None)
    
    # Renvoi vers la page login
    return redirect(url_for("login"))


@app.route("/", methods=["GET"])
@login_required
@templated("dashboard.html")
def index():
    """Fonction qui permet de récupérer le nom des appareils
    auxquels l'utilisateur a accès et de faire appel au template
    dédié à l'affichage de la page du dashboard"""

    # Récupération du nom des appareils auxquels l'utilisateur a accès
    session["appareils"] = get_seen_devices(session["username"])

    # Appel du template dashboard via décorateur avec paramètres
    return dict(
        appareils=session["appareils"],
        username=session["username"]
    )


@app.route("/change_password", methods=["POST"])
@login_required
@templated("dashboard.html")
def change_password():
    """Fonction qui permet à un utilisateur de modifier son mot de passe"""

    # Si la méthode de requête est POST
    if request.method == "POST":

        # Mofification du mot de passe par le nouveau
        result = change_psw(
            session["username"],
            request.form['new_psw'],
            request.form['new_psw2'],
            request.form['input_psw']
        )

        # Appel au template de la page dashboard avec paramètres
        return dict(
            appareils=session["appareils"],
            username=session["username"],
            error=result
        )


@app.route("/admin", methods=["GET"])
@admin_required
@templated('admin.html')
def admin():
    """Fonction qui permet de récupérer les données nécessaires
    à l'administrateur et de faire appel au template
    pour l'affichage de la page admin"""

    # Recupération des données à insérer dans les menus déroulants
    data = get_fields_data()
    types_app = [""] + data["types"]

    # Appel au template de la page admin avec paramètres
    return dict(
        postes=[""] + data["postes"],
        sites=data["sites"],
        chaines=data["chaines"],
        lignes=[""] + data["lignes"],
        types=types_app,
        nivs_resp=[""] + data['nivs_resp'],
        types_for_poste=types_app + ["TOUS"],
        utilisateurs=[user for user in data["utilisateurs"] if user != "admin"],
        appareils=data["appareils"],
        error=session.get("error")
    )


@app.route("/admin/add_user", methods=["POST"])
@admin_required
def add_user():
    """Fonction pour ajouter un utilisateur dans la base de données"""

    # Ajout du nouvel utilisateur avec les éléments entrés par l'admin
    # et instanciation de session["error"] pour affichage d'un message
    session["error"] = new_user(
        request.form["uname"],
        request.form['psw'],
        request.form['site'],
        request.form['chaine'],
        request.form['ligne'],
        request.form['poste']
    )

    # Rafraichissement de la page admin
    return redirect(url_for("admin"))


@app.route("/admin/delete_user", methods=["POST"])
@admin_required
def delete_user():
    """Fonction pour supprimer un utilisateur de la base de données"""

    # Suppression d'un utilisateur et instanciation
    # de session["error"] pour affichage d'un message de résultat
    session["error"] = del_user(request.form["uname"])

    # Rafraichissement de la page admin
    return redirect(url_for("admin"))


@app.route("/admin/change_password", methods=["POST"])
@admin_required
def change_user_password():
    """Fonction qui permet à l'administrateur de modifier
    mot de passe d'un utilisateur"""

    # Si la méthode de requête est POST
    if request.method == "POST":
        # Modification du mot de passe de l'utilisateur et instanciation 
        # de session["error"] pour affichage d'un message de résultat
        session['error'] = change_psw(
            request.form['username'],
            request.form['new_psw'],
            request.form['new_psw2']
        )
    # Rafraichissement de la page admin
    return redirect(url_for("admin"))


@app.route("/admin/add_device", methods=["POST"])
@admin_required
def add_device():
    """Fonction pour ajouter un appareil dans la base de données"""

    # Ajout du nouvel appareil avec les éléments entrés par l'admin
    # et instanciation de session["error"] pour affichage d'un message
    session["error"] = new_device(
        request.form["chaine"] + "_" + request.form["type"].split("_")[0],
        request.form["type"].split("_")[0],
        request.form["site"],
        request.form["chaine"],
        request.form["ligne"]
    )

    # Rafraichissement de la page admin
    return redirect(url_for("admin"))


@app.route("/admin/delete_device", methods=["POST"])
@admin_required
def delete_device():
    """Fonction pour supprimer un appareil de la base de données"""

    # Suppression d'un appareil et instanciation
    # de session["error"] pour affichage d'un message de résultat
    session["error"] = del_device(
        request.form["appareil"]
    )

    # Rafraichissement de la page admin
    return redirect(url_for("admin"))


@app.route("/admin/add_post_type", methods=["POST"])
@admin_required
def add_post_type():
    """Fonction pour ajouter un type d'appareil dans la base de données"""

    # Ajout du nouvel appareil avec les éléments entrés par l'admin
    # et instanciation de session["error"] pour affichage d'un message
    session["error"] = new_post_type(
        request.form["poste"],
        request.form["niv_resp"],
        request.form.getlist('type_for_poste')
    )

    # Rafraichissement de la page admin
    return redirect(url_for("admin"))


@app.route("/admin/delete_post_type", methods=["POST"])
@admin_required
def delete_post_type():
    """Fonction pour supprimer un poste de la base de données"""

    # Suppression d'un type d'appareils et instanciation
    # de session["error"] pour affichage d'un message de résultat
    session["error"] = del_post_type(
        request.form["poste"]
    )

    # Rafraichissement de la page admin
    return redirect(url_for("admin"))


@app.route("/admin/change_admin_password", methods=["POST"])
@admin_required
def change_admin_password():

    # Si la méthode de requête est POST
    if request.method == "POST":
        # Modification du mot de passe admin et instanciation 
        # de session["error"] pour affichage d'un message de résultat
        session['error'] = change_psw(
            "admin",
            request.form['new_psw'],
            request.form['new_psw2'],
            request.form['input_psw']
        )

    # Rafraichissement de la page admin
    return redirect(url_for("admin"))


@app.route('/chart-data')
@login_required
def chart_data():
    """Fonction qui permet de générer un flux streaming avec les données
    produites par les capteurs auxquels l'utilisateur connecté a accès"""

    # Récupération du nom des appareils auxquels l'utilisateur a accès
    appareils = session["appareils"]
    
    # Génération du flux streaming
    def generate_data():

        # Initialisation des datetimes des appareils à 0
        app_times = {}
        for app in appareils:
            app_times[app] = 0
        # Initialisation du nombre d'envoi de données par appareil à 0
        iter = 0
        # Instanciation d'une variable avec le nombre maximal de
        # valeurs inscrites dans les deques de X, Y et Z
        NB_VALUES = max([len(X[appareil]) for appareil in appareils])
        
        while True:
            # Prise en compte des données présentes dans les deques X, Y et Z
            # Ce morceau de code est valable surtout lors du lancement du serveur
            # dans le cas où tous les fichiers CSV produits par les capteurs
            # ne commencent pas au même datetime. Cela permet de faire en sorte
            # d'envoyer les données de manière cohérente, c'est-à-dire que les
            # valeurs envoyées en streaming aient le même datetime

            # Si le nombre d'iterations est inférieur au nombre de valeurs maximal
            if iter < NB_VALUES:
                # Initialisation du dictionnaire data
                data = {}
                # Pour tous les appreils accédés par l'utilisateur
                for appareil in appareils:
                    
                    i = NB_VALUES - len(X[appareil]) - iter + 1
                    # Si le nombre de données inscrites dans les deques de
                    # l'appareil concerné, ajouté au nombre d'envois de données
                    # est inférieur ou égal au nombre de valeurs maximal parmi
                    # les deques des autres autres appareils
                    if i > 0:
                        # Alors, instanciation de date avec des valeurs
                        # "nulles" permattant ensuite l'affichage de
                        # rien du tout sur le graphe de l'appareil
                        data[appareil] = {
                            'time': "",
                            'value' : "",
                            'anomaly' : 'null'
                        }

                    else:
                        # Sinon, envoi des données permettant l'affichage
                        # sur le graphe
                        data[appareil] = {
                            'time': str(X[appareil][-i]),
                            'value' : Y[appareil][-i],
                            'anomaly' : Z[appareil][-i]
                        }

                # Incrémentation de iter un fois tous les appareils traités
                # pour un datetime donné
                iter += 1
                # JSONification des données
                json_data = json.dumps(data)
                # Envoi des données
                yield f"data:{json_data}\n\n"
                # Faire une pause entre chaque envoi tout en faisant en sorte
                # que l'envoi de toutes les données d'un même datetime ne prenne
                # pas plus d'une seconde pour éviter tout décalage par la suite
                time.sleep(1 / (2 * QUELEN * ACC_FACT))

            # Une fois que les QUELEN données ont été envoyées
            # et affichées sur les graphes
            else:
                # Réinitialisation du dictionnaire data
                data = {}
                # Pour tous les appreils accédés par l'utilisateur
                for appareil in appareils:
                    # S'il existe une donnée pour l'appareil concerné
                    # et que le datetime récupéré et différent
                    # du datetime précédent
                    if len(X[appareil]) > 1 and \
                        X[appareil][-1] != app_times[appareil]:
                        # Instanciation de data avec les valeurs
                        # correspondant au datetime récupéré
                        data[appareil] = {
                            'time': str(X[appareil][-1]),
                            'value' : Y[appareil][-1],
                            'anomaly' : Z[appareil][-1]
                        }
                        # Enregistrement du datetime récupéré pour
                        # pouvoir le comparer avec le suivant
                        app_times[appareil] = X[appareil][-1]

                    # Sinon, s'il n'existe pas de donnée ou si
                    # le datetime récupéré est le même que le précédent
                    # (cas d'un capteur ne faisant pas des relevés
                    # toutes les secondes)
                    else:
                        # Alors, instanciation de date avec des valeurs
                        # "nulles" permattant ensuite l'affichage de
                        # rien du tout sur le graphe de l'appareil
                        data[appareil] = {
                            'time': "",
                            'value' : "",
                            'anomaly' : 'null'
                        }

                # JSONification des données
                json_data = json.dumps(data)
                # Envoi des données
                yield f"data:{json_data}\n\n"
                # Pause d'une seconde si le facteur d'accélération est de 1
                time.sleep(1 / ACC_FACT)

    return Response(generate_data(), mimetype="text/event-stream")


if __name__ == "__main__":
    app.run(debug=True)
