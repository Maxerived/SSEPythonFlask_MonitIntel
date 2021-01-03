import time

import requests

while True:
    requests.get("http://localhost:5000/input_data/light_a.tsv")
    time.sleep(0.2)
