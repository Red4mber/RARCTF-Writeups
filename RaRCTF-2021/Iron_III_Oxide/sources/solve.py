#/bin/python3
import json
from collections import Counter
from pwnlib.tubes import *
import re

#### INTERACT WITH THE PROGRAM

p = remote.remote("193.57.159.27", 50607)

p.recvline()
p.recvline()

#### GET EXPERIMENT RESULTS 

bonds = []
for i in range(0, 25):
    bonds.append([])
    for j in range(0, 24):
        l = p.recvline().decode()
        bonds_data = l[:-1].split(":")[1].split(',')[-3:]
        i1, i2 = (l[:-1].split(":")[0].split()[3], l[:-1].split(":")[0].split()[5])
        bonds_data = [x[1:] for x in bonds_data]
        bonds[i].append(bonds_data)


#### SEARCH IN BOND DICTIONNARY

path = "/home/amber/Workspace/rarctf/Misc/IronOxide/"
jsonpath = "bonds.json"

jsonfile = open(path+jsonpath, 'r')
bondDict = json.load(jsonfile)

def bondSearch(bonds, dict):
    results = []
    for b in bonds:
        for anumber, abonds in bondDict.items():
            for bnumber, data in abonds.items():
                if  b[0] == data['LinkType'] and \
                    b[1] == str(data['Diff1']) and \
                    b[2] == data['Diff2']:
                    results.append(anumber)
    return results

lab_key = ''
for b in bonds:
    lab_key = lab_key+chr(int(Counter(bondSearch(b, bondDict)).most_common(1)[0][0])+64)
print('lab_key = ', lab_key)
p.sendline(lab_key.encode())

f = p.recvall().decode()
r = re.compile('rarctf\{[\x20-\x7f]+\}')
print(r.findall(f)[0])

p.interactive()
