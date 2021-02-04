import dateutil.parser
import os
import sqlite3
import time
from collections import deque
from concurrent.futures import ThreadPoolExecutor

from pubsub import pub

# Détermine le nombre de valeurs glissantes dans les deques X, Y et Z
quelen = 2

# Détermine le facteur d'accélération d'envoi des données
acc_fact = 1

# Détermine le nombre de données envoyées
nb_data = 1000


def get_hash_from_db(identifiant):

    # Connexion à la base de données

    conn = sqlite3.connect("profils_utilisateurs.db")
    cur = conn.cursor()
    print("Connexion réussie à SQLite")

    # Récupération du hash_mdp à partir de l'identifiant

    cur.execute(
        "SELECT hash_mdp FROM utilisateurs WHERE identifiant = ?", (identifiant,)
    )
    res = cur.fetchall()

    # Fermeture de la base de données

    cur.close()
    conn.close()
    print("Connexion SQlite fermée")

    if len(res) == 0:
        return None

    return res[0][0]


def get_fields_data():

    # Connexion à la base de données

    conn = sqlite3.connect("profils_utilisateurs.db")
    cur = conn.cursor()
    print("Connexion réussie à SQLite")

    # Récupération des données

    postes = []
    cur.execute("SELECT poste FROM postes")
    res = cur.fetchall()
    for poste in res:
        postes.append(poste[0])

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

    # Fermeture de la base de données

    cur.close()
    conn.close()
    print("Connexion SQlite fermée")

    return [postes, sites, chaines, lignes, types, types_descr, nivs_resp]


def get_seen_devices(username):

    conn = sqlite3.connect("profils_utilisateurs.db")
    cur = conn.cursor()
    print("Connexion réussie à SQLite")

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
    type_app = res[1]

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
    print("Appareils de l'utilisateur {} récupérés".format(username))
    conn.close()
    print("Connexion SQlite fermée")

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


def send_appdata_after(delay, app, appdata):
    time.sleep(delay)
    pub.sendMessage(app, topic = app, data = appdata)
    

def send_data(data, app, nb_data):

    date_time = [None, None]
    date_time[0] = dateutil.parser.parse(data[app][0][:-1].split(',')[0])
    send_appdata_after(0, app, data[app][0][:-1])

    for i in range(1, nb_data):
        date_time[1] = dateutil.parser.parse(data[app][i][:-1].split(',')[0])
        sleep_time = (date_time[1] - date_time[0]).seconds / acc_fact
        date_time[0] = date_time[1]
        send_appdata_after(sleep_time, app, data[app][i][:-1])


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


nb_sendjobs = len(apps) * nb_data
executor = ThreadPoolExecutor(nb_sendjobs)

for app in apps:
    executor.submit(send_data, data, app, nb_data)


##########################################################################################
"""
async def send_appdata_after(delay, app, data):
    await asyncio.sleep(delay)
    pub.sendMessage(app, topic = app, data = data)
    

async def send_data(data, apps, nb_data):

    date_time = {}
    sleep_time = {}
    tasks = {}
    for app in apps:
        date_time[app] = [None, None]
        date_time[app][0] = datetime.strptime(data[app][0][:-2].split(',')[0], "%d/%m/%Y %H:%M:%S")
        sleep_time[app] = [0]
        tasks[app] = [asyncio.create_task(send_appdata_after(sleep_time[app][0], app, data[app][0][:-2]))]
        for i in range(1, nb_data):
            date_time[app][1] = datetime.strptime(data[app][i][:-2].split(',')[0], "%d/%m/%Y %H:%M:%S")
            sleep_time[app].append((date_time[app][1] - date_time[app][0]).seconds / acc_fact)
#            date_time[app][0] = date_time[app][1]
            tasks[app].append(asyncio.create_task(
                send_appdata_after(sleep_time[app][i], app, data[app][i][:-2]))
            )

    for i in range(nb_data):
        for app in apps:
            await tasks[app][i]

asyncio.run(send_data(data, apps, nb_data))
"""
