import sseclient
from pubsub import pub


messages = sseclient.SSEClient("http://localhost:5000/listen")


conn = sqlite3.connect("profils_utilisateurs.db")
cur = conn.cursor()
print("Connexion réussie à SQLite")

# Récupération des données

postes = []
cur.execute("SELECT poste FROM postes")
res = cur.fetchall()
for poste in res:
    postes.append(poste[0])

def listener(data = "foo"):
    print(data)

for topic in topics:
    pub.subscribe(listener, topic)

for msg in messages:
    pub.sendMessage("topic_1", data = msg.data)
