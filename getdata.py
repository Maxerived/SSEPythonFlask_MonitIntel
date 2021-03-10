import dateutil.parser
import os
import sqlite3
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor

from pubsub import pub

# Détermine le nombre de valeurs glissantes dans les deques X, Y et Z
quelen = 100

# Détermine le facteur d'accélération d'envoi des données
acc_fact = 1

# Détermine le nombre de données envoyées
nb_data = 2000


def get_fields_data():

    # Connexion à la base de données
    conn = sqlite3.connect("profils_utilisateurs.db")
    cur = conn.cursor()
    print("[INFO] Connexion réussie à SQLite")

    # Récupération des données
    postes = []
    cur.execute("SELECT poste,niveau_de_responsabilite FROM postes")
    postes = cur.fetchall()

    sites = []
    cur.execute("SELECT site FROM sites")
    res = cur.fetchall()
    for site in res:
        sites.append(site[0])
    
    chaines = []
    cur.execute("SELECT chaine,site FROM chaines")
    res = cur.fetchall()
    # [('A1', 'A'), ('B1', 'B'), ('B2', 'B'), ('B3', 'B'), ('C1', 'C'), ('C2', 'C')]
    chaines = res

    lignes = []
    cur.execute("SELECT ligne FROM lignes")
    res = cur.fetchall()
    for ligne in res:
        lignes.append(ligne[0])
    
    types = []
    cur.execute("SELECT type_appareil FROM types_appareil")
    res = cur.fetchall()
    for type_appareil in res:
        types.append(type_appareil[0])
    
    types_descr = []
    cur.execute("SELECT description FROM types_appareil")
    res = cur.fetchall()
    for type_descr in res:
        types_descr.append(type_descr[0])
    
    nivs_resp = []
    cur.execute("SELECT niv_resp FROM niveau_resp")
    res = cur.fetchall()
    for niv_resp in res:
        nivs_resp.append(niv_resp[0])

    utilisateurs = []
    cur.execute("""SELECT identifiant FROM utilisateurs""")
    res = cur.fetchall()
    for utilisateur in res:
        utilisateurs.append(utilisateur[0])

    # Fermeture de la base de données
    cur.close()
    conn.close()
    print("[INFO] Connexion SQlite fermée")

    return {
        "postes": postes,
        "sites" : sites,
        "chaines" : chaines,
        "lignes" : lignes,
        "types" : types,
        "types_descr" : types_descr,
        "nivs_resp" : nivs_resp,
        "utilisateurs" : utilisateurs
    }


def get_seen_devices(username):

    conn = sqlite3.connect("profils_utilisateurs.db")
    cur = conn.cursor()
    print("[INFO] Connexion réussie à SQLite")

    # Récupération du poste tenu par l'utilisateur
    cur.execute(
        "SELECT site, chaine_service, ligne_de_production, \
        poste_tenu FROM utilisateurs WHERE identifiant = ?",
        (username,),
    )
    res = cur.fetchall()[0]
    site = res[0]
    chaine = res[1]
    ligne = res[2]
    poste = res[3]

    # Récupération des types d'appareil en visibilité par l'utilisateur
    cur.execute(
        "SELECT niveau_de_responsabilite, appareils_vus FROM postes \
        WHERE poste = ?",
        (poste,),
    )
    res = cur.fetchall()[0]
    niv_resp = res[0]
    type_app = res[1] # type d'appareil(s) vu(s) par un utilisateur occupant le poste considéré
    # Va falloir modifier si on réussit à séléctionner plusieurs appareils
    types_app = []

    if type_app == "TOUS":
        cur.execute("SELECT type_appareil FROM types_appareil")
        res = cur.fetchall()
        for type_a in res:
            types_app.append(type_a[0])
    else:
        types_app.append(type_app)

    res = []
    for type_app in types_app:
        if niv_resp == "direction générale":
            cur.execute("SELECT appareil FROM appareils WHERE type = ?", (type_app,))
        elif niv_resp == "site":
            cur.execute(
                "SELECT appareil FROM appareils \
                WHERE type = ? AND site_de_production = ?",
                (type_app, site),
            )
        elif niv_resp == "chaine":
            cur.execute(
                "SELECT appareil FROM appareils WHERE type = ? \
                AND site_de_production = ? \
                AND chaine_de_production = ?",
                (type_app, site, chaine),
            )
        elif niv_resp == "ligne":
            cur.execute(
                "SELECT appareil FROM appareils WHERE type = ? \
                AND site_de_production = ? \
                AND chaine_de_production = ? \
                AND ligne_de_production = ?",
                (type_app, site, chaine, ligne),
            )
        res.append(cur.fetchall())

    cur.close()
    print("[INFO] Appareils de l'utilisateur {} récupérés".format(username))
    conn.close()
    print("[INFO] Connexion SQlite fermée")

    appareils = []
    for i in range(len(res)):
        for j in range(len(res[i])):
            appareils += res[i][j]

    return appareils


def listener(topic = None, data = None):
    date_time = dateutil.parser.parse(data.split(',')[0])
    X[topic].append(date_time)
    value = data.split(",")[1]
    Y[topic].append(value)
    anomaly = data.split(',')[2]
    Z[topic].append(anomaly.lower())
#    print(topic, X[topic], Y[topic], Z[topic])


def send_appdata_after(delay, app, app_data):
    time.sleep(delay)
    pub.sendMessage(app, topic = app, data = app_data)
    

def send_data(app_data, app, nb_data, time_before_sending):

    time.sleep(time_before_sending / acc_fact)

    date_time = [None, None]
    date_time[0] = dateutil.parser.parse(app_data[0][:-1].split(',')[0])
    send_appdata_after(0, app, app_data[0][:-1])

    for i in range(1, nb_data):
        date_time[1] = dateutil.parser.parse(app_data[i][:-1].split(',')[0])
        sleep_time = (date_time[1] - date_time[0]).seconds / acc_fact
        date_time[0] = date_time[1]
        send_appdata_after(sleep_time, app, app_data[i][:-1])



X = {}
Y = {}
Z = {}
appareils = []
new_apps = get_seen_devices("alix")
for appareil in appareils:
    if appareil not in new_apps:
        for K in [X, Y, Z]:
            K.pop(appareil)
for appareil in new_apps:
    if appareil not in appareils:
        for K in [X, Y, Z]:
            K[appareil] = deque(maxlen = quelen)
appareils = new_apps


data = {}
apps = []
for appareil in appareils:
    pub.subscribe(listener, appareil)
    filepath = "devices_data/" + appareil + ".csv"
    if appareil not in apps and os.path.isfile(filepath):
        apps.append(appareil)
        with open(filepath, "r") as f:
            data[appareil] = f.readlines()
        filehead_time = dateutil.parser.parse(data[appareil][1].split(',')[0])
        filetail_time = dateutil.parser.parse(data[appareil][-1].split(',')[0])
        if filetail_time < filehead_time:
            data[appareil].reverse()
            if len(data[appareil]) < nb_data:
                data[appareil] = data[appareil][:-1]
            data[appareil] = data[appareil][:-1][:nb_data]
        elif filetail_time > filehead_time:
            if len(data[appareil]) < nb_data:
                data[appareil] = data[appareil][1:]
            data[appareil] = data[appareil][1:][:nb_data]
    if appareil in apps and not os.path.isfile(filepath):
        data.pop(appareil)
        apps.remove(appareil)


# Récupération des horaires de la première donnée de chaque capteur
# et tri des appareils dans l'ordre chronologique
sending_times = {}
for app in apps:
    sending_times[app] = dateutil.parser.parse(data[app][0].split(',')[0])
time_sorted_tuples = sorted(sending_times.items(), key=lambda t:t[1])
time_sorted_list = [time_sorted_tuples[i][0] for i in range(len(time_sorted_tuples))]

# Simulation d'envoi des données depuis les capteurs
# de manière simultanée et coordonnée en fonction de
# l'horaire de la première donnée du capteur
sending_time = min([time_sorted_tuples[i][1] for i in range(len(time_sorted_tuples))])
executor = ThreadPoolExecutor(len(apps))
executor.submit(send_data, data[time_sorted_list[0]], time_sorted_list[0], nb_data, 0)
print("[INFO] Connexion au capteur", time_sorted_list[0])
for app in time_sorted_list[1:]:
    sleep_time = (sending_times[app] - sending_time).seconds
    executor.submit(send_data, data[app], app, nb_data, sleep_time)
    print("[INFO] Connexion au capteur", app)
    sending_time = sending_times[app]



