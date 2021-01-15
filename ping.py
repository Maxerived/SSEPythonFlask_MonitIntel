import time
import requests
import 

'''
while True:
    requests.get("http://localhost:5000/input_data/light_a.tsv")
    time.sleep(0.2)
'''
'''
for file in ["B1_P1.csv", "B1_P2.csv", "B1_T1.csv", "B2_T1.csv"]:
    with open("Données_capteurs/" + file, 'r') as f:
        lines = f.readlines()
    new_lines = []
    i = 0
    for line in lines:
        i += 1
        if i % 2 == 1:
            new_lines.append(line)
for file in ["B1_P1.csv", "B1_P2.csv", "B1_T1.csv", "B2_T1.csv"]:
    with open("Données_capteurs/" + file, 'w') as f:
        for line in new_lines:
            f.write(line)
'''

def tsv_to_csv(filepath):

    with open(filepath, 'r') as file:
        lines = file.readlines()
    
    new_lines =[]
    for line in lines:
        line = ';'.join(line.split("\t"))
        new_lines.append(line)
    
    if filepath.rsplit('.', 1)[1].lower() == "tsv":
        new_filepath = filepath.rsplit('.', 1)[0] + ".csv"
    else:
        new_filepath = filepath + ".csv"
    
    with open(new_filepath, 'w') as file:
        for line in new_lines:
            file.write(line)


