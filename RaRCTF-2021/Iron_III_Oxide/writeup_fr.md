# Iron(III) Oxide writeup

## Comprendre le programme

L'application est plutôt simple, une fois lancée, elle affiche les résultats d'une expérience :

![](./screenshots/experiment.png)


L'experience est assez simple, le programme choisis 25 atomes aléatoirement et va afficher les liaisons entre ces atomes

Ensuite, le programme demande la clef du labo, 

![](./screenshots/ask_lab_key.png)

Si on donne la bonne clef, on a le flag.

Maintenant, regardons le code : 

J'ai tout de suite jeté un oeil à la fonction `print_flag()`, mais elle est appelée une seule fois, et c'est après avoir donné la clef du labo, et seulement si elle est valide.

Je continue donc mon chemin en remontant le code, et jette un oeil a cette clef du labo

Il s'agit d'une chaine de 25 caractères imprimables aléatoires, générées avec un générateur sécurisé.

![](./screenshots/labkey_generation.png)

En revanche, il y a un endroit ou cette clef est utilisée
Elle est utilisée afin de générer le "chem_password" qui est la liste des atomes utilisés dans l'expérience !
```rust
let chem_password: Vec<Atom> = lab_key
    .as_bytes()
    .iter()
    .map(|x| Atom::from_atomic_number(*x - 64, &elements).unwrap())
    .collect();
```
Cela veut dire que si on arrive à inverser l'expérience, a récuperer les atomes depuis leurs liaisons, nous pouvons récuperer le chem_password, et donc la clef du labo !

## Intéragir avec le programme

Dans un premier temps, nous avons besoin d'un moyen d'interagir avec le programme.
J'ai donc choisi Python, afin d'utiliser les tubes de pwnlib pour interagir avec l'executable et les serveurs du ctf avec le même script.

Le script va donc lancer l'executable, puis lire les résultats de l'experience afin de tout stocker dans un tableau.

```python
from pwnlib.tubes import *

debug = True

path = "/home/amber/Workspace/rarctf/Misc/IronOxide/"
exe = "IronOxide"

#p = remote.remote("193.57.159.27", 50607)
p = process.process(executable=path+exe, cwd=path, argv="")

p.recvline()    # Generating lab key...
p.recvline()    # Doing experiment...

bonds = []
for i in range(0, 25):
    bonds.append([])
    for j in range(0, 24): # Seulement 24 car l'expérience ne donne pas les liaisons d'un atomes avec lui même
        l = p.recvline().decode()[:-1]
        # Récupérer uniquement les 3 derniers champs, séparés par des virgules
        bonds_data = l.split(":")[1][1:].split(',')[-3:]

        # Nettoyer les espaces en début de chaine
        bonds_data = [x[1:] for x in bonds_data]

        # Ajoute les données au tableau
        bonds[i].append(bonds_data)
```

Cela nous donne donc un tableau ayant ce format là :
```python
[
    [ # Atome 1
        ["Type de liaison", "Difference1", "Difference2"], # Liaison atome 1 et atome 2
        ["Type de liaison", "Difference1", "Difference2"], # Liaison atome 1 et atome 3
        ["Type de liaison", "Difference1", "Difference2"], # Liaison atome 1 et atome 4
        ["Type de liaison", "Difference1", "Difference2"], # Liaison atome 1 et atome 5
        ["Type de liaison", "Difference1", "Difference2"], # Liaison atome 1 et atome 6
        [....]
    ],
    [ # Atome 2
        ["Type de liaison", "Difference1", "Difference2"], # Liaison atome 2 et atome 1
        ["Type de liaison", "Difference1", "Difference2"], # Liaison atome 2 et atome 3
        [....]
    ],
    [....]
]
```
## Créer un dictionnaire de liaisons

Maintenant que nous avons un moyen d'interagir avec le programme et de récupérer les résultats de l'expérience,
Il nous faut un moyen de determiner a quel atome correspond une liaison.
Le moyen le plus simple de faire une telle chose revient a créer un dictionnaire de liaisons,
Un grand fichier json, contenant toutes les liaisons possibles, dans lequel nous pourrions rechercher une liaison particulière afin de determiner quels atomes la compose. 

L'experience nous donne trois informations cruciales: 
 - Le type de liaison ("Pas de réaction" | "Liaison covalente" | "Liaison Ionique" | "Liaison Metallique")
 - La différence absolue entre le numéro atomique des deux atomes
 - La différence absolue entre la valeur d'electronegativité des deux atomes

On a aussi un identifiant pour chaque atome inconnu, mais je n'en aurais pas besoin 

J'ai donc écrit du code, et copié celui de l'experience, afin de refaire l'experience non pas sur 25 atomes aléatoires, mais sur les 104 atomes, me donnant ainsi toutes les liaisons possibles, et stocker les résultats dans une structure que je vais ensuite exporter dans un fichier json.

Le code a été ajouté dans la fonction `main` juste avant la boucle for qui demande la clef du labo.

> Le code est pas terrible
>
> Mais c'est la première fois que je touche a rust, je suppose que j'ai une excuse

```rust
    use std::collections::HashMap;
    use serde::Serialize;
    use arrayvec::ArrayString; // Arraystring necessaire car la taille d'une str classique serait inconnue a la compilation

    let atomvec: Vec<Atom> = elements.iter().map(|e| Atom::from_element(&e)).collect();
    let mut genbonds = HashMap::new();

    #[derive(Serialize)]
    struct s_Bond {
        BondType: ArrayString<16>,
        Diff1: i16,
        Diff2: ArrayString<8>,
    }
    for i in 0..103 {
        let a = &atomvec[i];
        let mut abonds = HashMap::new();
        for j in 0..103 {
            if i == j {
                continue;
            }
            let first = &a;
            let second = &atomvec[j];
            let difference1 =
                (first.element.atomicnumber as i16 - second.element.atomicnumber as i16).abs();
            let difference2 =
                (first.element.electronegativity - second.element.electronegativity).abs();
            let bond = Bond::new(first, second);
            let mut s = ArrayString::<16>::new();
            match bond {
                Some(thebond) => {
                    s.push_str(&format!("{:?}", thebond.bondtype));
                }
                None => {
                    s.push_str("No Reaction");
                }
            }
            let mut d = ArrayString::<8>::new();
            // Diff2 est une chaine de caractère, afin d'assurer d'avoir le même format que dans l'experience
            d.push_str(&format!("{:.2}", difference2)); 
            let l = s_Bond {
                BondType: s,
                Diff1: difference1,
                Diff2: d,
            };
            abonds.insert(second.element.atomicnumber, l);
        }
        genbond.insert(a.element.atomicnumber, abonds);
    }
    let serialized = serde_json::to_string(&genbond).unwrap();
    ::serde_json::to_writer(&File::create("data.json")?, &serialized)?;
```
Ajouter ceci cargo.toml, afin d'inclure les nouvelles dépendances
```toml
serde_json = "1.0"
arrayvec = {version = "0.7", features = ["serde"]}
```
On compile avec la commande `cargo build`

On lance le nouvel executable, et si tout se passe bien, un fichier `data.json` devrais avoir été créé.

Le fichier n'est pas propre, il faut retirer les '\' et reformatter le document, mais vscode fait ca facilement alors je n'ai pas besoin de réparer mon code.

Après avoir nettoyé le fichier, on obtient un dictionnaire ayant cette structure :

```json
{
	"1": {
		"2": {
			"LinkType": "No Reaction",
			"Diff1": 1,
			"Diff2": "NaN"
		},
		"3": {
			"LinkType": "Metallic",
			"Diff1": 2,
			"Diff2": "1.22"
		},
		"4": {
			"LinkType": "Metallic",
			"Diff1": 3,
			"Diff2": "0.63"
		},
```
chaque clef est le numéro atomique d'un atome,

donc `dictionnary["2"]["34"]` est la liaison entre l'hélium et le selenium

## Chercher dans le dictionnaire

J'ai rapidement fait une fonction permettant de rechercher une liaison dans cet immense json 

Elle va regarder dans tout le fichier, et a chaque fois qu'elle trouve la liaison qu'elle cherche, 
va ajouter le numéro atomique des atomes concernés dans un tableau
A la fin de la fonction, un Counter va compter les atomes du tableau et renvoyer le plus courant,

Le seul atom présent 25 fois dans l'array doit etre l'atome recherché, alors on renvoie celui ci


```python
import json
from collections import Counter

path = "/home/amber/Workspace/rarctf/Misc/IronOxide/"
jsonpath = "bonds.json"
test = [['Metallic', '1', '0.02'], ['Metallic', '19', '0.10'], ['Metallic', '37', '0.24'], ['Metallic', '39', '0.30'], ['Metallic', '54', '0.45'], ['Metallic', '45', '0.49'], ['Metallic', '28', '0.53'], ['Metallic', '28', '0.53'], ['Metallic', '28', '0.53'], ['Metallic', '10', '0.57'], ['Metallic', '27', '0.69'], ['Metallic', '29', '0.78'], ['Metallic', '44', '0.78'], ['Metallic', '11', '0.81'], ['Metallic', '6', '0.98'], ['Metallic', '6', '0.98'], ['Metallic', '16', '1.04'], ['Ionic', '43', '1.07'], ['Ionic', '43', '1.07'], ['Metallic', '12', '1.08'], ['Metallic', '57', '1.08'], ['Metallic', '13', '1.16'], ['No Reaction', '22', '1.88'], ['No Reaction', '22', '1.88']]

jsonfile = open(path+jsonpath, 'r')
bondDict = json.load(jsonfile)

def getAtom(bonds, dict):
    results = []
    for b in bonds:
        for anumber, abonds in bondDict.items():
            for bnumber, data in abonds.items():
                if  b[0] == data['LinkType'] and \
                    b[1] == str(data['Diff1']) and \
                    b[2] == data['Diff2']:
                    results.append(anumber)
    return Counter(results).most_common(1)[0][0]

print(getAtom(test, bondDict))
```

J'ajoute donc cette fonction au premier script, je la lance avec les liaisons données apr l'expérience et j'ai la liste des atomes de l'expérience !
![](./screenshots/getAtoms.png)

Nous avons donc le chem_password ! Il nous faut maintenant en dériver la clef du laboratoire

## La clef du labo 

On sait que le chem password est dérivé de la clef du labo
`lab_key[x] - 64 = chem_password[x]` 

Pas besoin d'être un génie pour comprendre qu'on peut inverser l'opération :
`chem_password[x] + 64 = lab_key[x]`

Ensuite il nous suffit d'utiliser chr, pour récuperer le caractère associé :

```python
lab_key = ''
for b in bonds:
    atomicnumber = int(bondSearch(b, bondDict))
    lab_key = lab_key+chr(atomicnumber+64)

print('lab_key = ', lab_key)
```

Je n'ai plus qu'a l'envoyer avec : `p.sendline(lab_key.encode())`

Et le programme me donne le flag ! 
![](./screenshots/flag.png)
