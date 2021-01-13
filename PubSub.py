import time
import sqlite3
import sys
from collections import deque
from datetime import datetime
from matplotlib import dates
from pubsub import pub

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


def sub_to_devices(username):

    devices = get_devices_seen(username)
    for device in devices:
        pub.subscribe(listener, device)


X = {}
Y = {}
appareils = get_devices_seen("alix")
for appareil in appareils:
    X[appareil] = deque(maxlen = 5)
    Y[appareil] = deque(maxlen = 5)


def listener(topic = None, data = None):
    date_time = datetime.strptime(data.split(';')[0], "%d/%m/%Y %H:%M")
    X[topic].append(dates.date2num(date_time))
    value = data.split(';')[1]
    Y[topic].append(value)
    anomaly = data.split(';')[2]
    print(X[topic], Y[topic])


sub_to_devices("sacha")

if sys.argv[1] is not None:
    filepath = sys.argv[1]
    filename = filepath.rsplit('/', 1)[-1]
    if filename.rsplit('.', 1)[1] == "csv":
        topic = filename.rsplit('.', 1)[0]
    else:
        topic = filename

with open(filepath, "r") as file:
    lines = file.readlines()

if len(lines) <= 2:
    date_time = None
    value = None
    anomaly = None
else:
    #header = lines[0]
    #var = header.split()[1]
    filehead_time = datetime.strptime(lines[1].split(';')[0], "%d/%m/%Y %H:%M")
    filetail_time = datetime.strptime(lines[-1].split(';')[0], "%d/%m/%Y %H:%M")
    if filetail_time < filehead_time:
        lines.reverse()
        lines = lines[:-1]
    elif filetail_time > filehead_time:
        lines = lines[1:]

    date_time = [None, None]
    pub.sendMessage(topic, topic = topic, data = lines[0][:-2])
    date_time[0] = datetime.strptime(lines[0][:-2].split(';')[0], "%d/%m/%Y %H:%M")
    
    for i in range(1, 10):
        date_time[1] = datetime.strptime(lines[i][:-2].split(';')[0], "%d/%m/%Y %H:%M")
        time.sleep((date_time[1]-date_time[0]).seconds/60)
        date_time[0] = date_time[1]
        pub.sendMessage(topic, topic = topic, data = lines[i][:-2])


