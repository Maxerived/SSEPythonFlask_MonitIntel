import flask, json, queue
from datetime import datetime

app = flask.Flask(__name__)

@app.route('/')
def index():
    return flask.render_template('auth.html')

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
    msg = f'data: {data}\n\n'
    if event is not None:
        msg = f'event: {event}\n{msg}'
    return msg


@app.route('/input_data/<input_data>')
def get_values(input_data):
	input_data = str(input_data)
	input_var_elem = input_data.rsplit('.', 1)
	var = input_var_elem[0]
	if len(input_var_elem) > 1:
		extension = input_data.rsplit('.', 1)[1].lower()
		if extension not in {"csv", "tsv"}:
			return {"La ressource n'est pas au bon format"}, 200
		filename = input_data
		with open(filename, 'r') as file :
			lines = file.readlines()
			header = lines[0]
			mesured_var = header.split()[1]
#			print(mesured_var)
			filestart_time = datetime.strptime(" ".join(lines[1].split()[:2]), '%Y-%m-%d %H:%M:%S.%f')
			fileend_time = datetime.strptime(" ".join(lines[-1].split()[:2]), '%Y-%m-%d %H:%M:%S.%f')
			if fileend_time < filestart_time:
				data = lines[-1].split()[2]
				lines = lines[:-1]
			elif fileend_time > filestart_time:
				data = lines[1].split()[2]
				lines = [header] + lines[2:]
		file = open(filename, 'w')
		file.write(''.join(lines)[:-1])
		file.close()
		msg = format_sse(data=data)
		announcer.announce(msg=msg)
	return flask.jsonify({"Status" : "On progress..."}), 200


@app.route('/listen', methods=['GET'])
def listen():

    def stream():
        messages = announcer.listen()  # returns a queue.Queue
        while True:
            msg = messages.get()  # blocks until a new message arrives
            yield msg

    return flask.Response(stream(), mimetype='text/event-stream')








