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

        result = check_credentials(
            request.form["uname"],
            request.form["psw"]
        )

        # Si les credntials sont incorrects
        if result is not "OK":
            return dict(error=result)

        session["username"] = request.form["uname"]

        # Si l'utilisateur est admin
        if request.form["uname"] == "admin":
            return redirect(url_for("admin"))

        # Pour un utilisateur lambda
        return redirect(url_for("index"))


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

    return dict(
        appareils=session["appareils"],
        username=session["username"]
    )


@app.route("/change_password", methods=["POST"])
@login_required
@templated("dashboard.html")
def change_password():

    if request.method == "POST":

        result = change_psw(
            session["username"],
            request.form['new_psw'],
            request.form['new_psw2'],
            request.form['input_psw']
        )

        return dict(
            appareils=session["appareils"],
            username=session["username"],
            error=result
        )


@app.route("/admin", methods=["GET"])
@admin_required
@templated('admin.html')
def admin():

    # Recupération des données à insérer dans les menus déroulants

    data = get_fields_data()
    types = [""] + data["types"]
    types_descr = [""] + data["types_descr"]
    
    types_app = [""]
    for i in range(1, len(types)):
        types_app.append(types[i] + "_" + types_descr[i])

    return dict(
        postes=[""] + data["postes"],
        sites=data["sites"],
        chaines=data["chaines"],
        lignes=[""] + data["lignes"],
        types=types_app,
        nivs_resp=[""] + data['nivs_resp'],
        types_for_poste=types_app + ["TOUS"],
        utilisateurs=data["utilisateurs"][1:],
        error=session.get("error")
    )


@app.route("/admin/add_user", methods=["POST"])
@admin_required
def add_user():
    """Fonction pour ajouter un utilisateur dans la base de données"""

    session["error"] = new_user(
        request.form["uname"],
        request.form['psw'],
        request.form['site'],
        request.form['chaine'],
        request.form['ligne'],
        request.form['poste']
    )

    return redirect(url_for("admin"))


@app.route("/admin/delete_user", methods=["POST"])
@admin_required
def delete_user():
    """Fonction pour supprimer un utilisateur de la base de données"""

    session["error"] = del_user(request.form["uname"])

    return redirect(url_for("admin"))


@app.route("/admin/change_password", methods=["POST"])
@admin_required
def change_user_password():

    if request.method == "POST":

        session['error'] = change_psw(
            request.form['username'],
            request.form['new_psw'],
            request.form['new_psw2']
        )

    return redirect(url_for("admin"))


@app.route("/admin/add_device", methods=["POST"])
@admin_required
def add_device():
    """Fonction pour ajouter un appareil dans la base de données"""

    session["error"] = new_device(
        request.form["chaine"] + "_" + request.form["type"].split("_")[0],
        request.form["type"].split("_")[0],
        request.form["site"],
        request.form["chaine"],
        request.form["ligne"]
    )

    return redirect(url_for("admin"))


@app.route("/admin/add_post_type", methods=["POST"])
@admin_required
def add_post_type():
    """Fonction pour ajouter un type d'appareil dans la base de données"""

    session["error"] = new_post_type(
        request.form["poste"],
        request.form["niv_resp"],
        request.form.getlist('type_for_poste')
    )

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


if __name__ == "__main__":
    app.run(debug=True, ssl_context=("cert.pem", "key.pem"))
