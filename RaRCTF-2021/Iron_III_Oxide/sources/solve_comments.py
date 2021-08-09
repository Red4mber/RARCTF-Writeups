#/bin/python3
import json
from collections import Counter
from pwnlib.tubes import *
import re


# Will search in the bond dictionnary to guess the atom
def bondSearch(bonds, dict):
    results = []
    for b in bonds:
        for anumber, abonds in bondDict.items():
            for bnumber, data in abonds.items():
                if  b[0] == data['LinkType'] and \
                    b[1] == str(data['Diff1']) and \
                    b[2] == data['Diff2']:
                    results.append(anumber)
    return Counter(results).most_common(1)[0][0]      #Return only the atomic number 


path = "/home/amber/Workspace/rarctf/Misc/IronOxide/"
jsonpath = "bonds.json"


#### INTERACT WITH THE PROGRAM
p = remote.remote("193.57.159.27", 50607)

p.recvline()    # Generating lab key...
p.recvline()    # Doing experiment...


#### GET EXPERIMENT RESULTS 
bonds = []
for i in range(0, 25):
    bonds.append([])
    for j in range(0, 24):
        # Get the line
        l = p.recvline().decode()[:-1]
        # Extract the three last fields separated by a comma
        bonds_data = l.split(":")[1][1:].split(',')[-3:]
        # Remove the leading space 
        bonds_data = [x[1:] for x in bonds_data]
        # Add it to an array
        bonds[i].append(bonds_data)

# Open the bond dictionary
jsonfile = open(path+jsonpath, 'r')
bondDict = json.load(jsonfile)

# generate the lab key
lab_key = ''
for b in bonds:
    lab_key = lab_key+chr(int(Counter(bondSearch(b, bondDict)))+64)
print('lab_key = ', lab_key)

# Send the key 
p.sendline(lab_key.encode())


# This part is totally unnecessary 
# but i like to have a clean output
f = p.recvall().decode()
r = re.compile('rarctf\{[\x20-\x7f]+\}')
print(r.findall(f)[0])
