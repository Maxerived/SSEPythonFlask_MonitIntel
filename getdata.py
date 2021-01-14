import asyncio
import os
import time
import sqlite3
from collections import deque
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from matplotlib import dates
from pubsub import pub

# Détermine le nombre de valeurs glissantes prises en compte pour le graphe
quelen = 5

# Détermine le facteur d'accélération d'afficahe des données
acc_fact = 1

# Détermine le nombre de données envoyées
nb_data = 20


def get_devices_seen(username):

    conn = sqlite3.connect("profils_utilisateurs.db")
    cur = conn.cursor()
    print("Connexion réussie à SQLite")

    # Récupération du poste tenu par l'utilisateur

    cur.execute("SELECT site, chaine_service, ligne_de_production, poste_tenu FROM utilisateurs WHERE identifiant = ?", (username,))
    res = cur.fetchall()[0]
    site = res[0]
    chaine = res[1]
    ligne = res[2]
    poste = res[3]

    # Récupération des types d'appareil en visibilité par l'utilisateur

    cur.execute("SELECT niveau_de_responsabilite, appareils_vus FROM postes \
        WHERE poste = ?", (poste,))
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
            cur.execute("SELECT appareil FROM appareils \
                WHERE type = ? AND site_de_production = ?", (type_app, site))
        elif niv_resp == "chaine":
            cur.execute("SELECT appareil FROM appareils WHERE type = ? \
                AND site_de_production = ? \
                AND chaine_de_production = ?", (type_app, site, chaine))
        elif niv_resp == "ligne":
            cur.execute("SELECT appareil FROM appareils WHERE type = ? \
                AND site_de_production = ? \
                AND chaine_de_production = ? \
                AND ligne_de_production = ?", (type_app, site, chaine, ligne))
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


X = {}
Y = {}
Z = {}
appareils = get_devices_seen("alix")
for appareil in appareils:
    X[appareil] = deque(maxlen = quelen)
    Y[appareil] = deque(maxlen = quelen)
    Z[appareil] = deque(maxlen = quelen)


def listener(topic = None, data = None):
    date_time = datetime.strptime(data.split(',')[0], "%d/%m/%Y %H:%M:%S")
    X[topic].append(dates.date2num(date_time))
    value = data.split(',')[1]
    Y[topic].append(value)
    anomaly = data.split(',')[2]
    Z[topic].append(value)
    print(topic, X[topic], Y[topic], Z[topic])


data = {}
apps = []
for appareil in appareils:
    pub.subscribe(listener, appareil)
    filepath = "devices_data/" + appareil + ".csv"
    if os.path.isfile(filepath):
        apps.append(appareil)
        with open(filepath, "r") as f:
            data[appareil] = f.readlines()
        filehead_time = datetime.strptime(data[appareil][1].split(',')[0], "%d/%m/%Y %H:%M:%S")
        filetail_time = datetime.strptime(data[appareil][-1].split(',')[0], "%d/%m/%Y %H:%M:%S")
        if filetail_time < filehead_time:
            data[appareil].reverse()
            data[appareil] = data[appareil][:-1][:nb_data]
        elif filetail_time > filehead_time:
            data[appareil] = data[appareil][1:][:nb_data]


max_data = min(len(data[app]) for app in apps)

nb_sendjobs = len(apps)*nb_data
executor = ThreadPoolExecutor(nb_sendjobs)

'''
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
'''

def send_appdata_after(delay, app, data):
    time.sleep(delay)
    pub.sendMessage(app, topic = app, data = data)
    

def send_data(data, app, nb_data):

    date_time = [None, None]
    date_time[0] = datetime.strptime(data[app][0][:-2].split(',')[0], "%d/%m/%Y %H:%M:%S")
    send_appdata_after(0, app, data[app][0][:-2])

    for i in range(1, nb_data):
        date_time[1] = datetime.strptime(data[app][i][:-2].split(',')[0], "%d/%m/%Y %H:%M:%S")
        sleep_time = (date_time[1] - date_time[0]).seconds / acc_fact
        date_time[0] = date_time[1]
        send_appdata_after(sleep_time, app, data[app][i][:-2])

for app in apps:
    executor.submit(send_data, data, app, nb_data)



