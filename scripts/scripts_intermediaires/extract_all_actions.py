from bs4 import BeautifulSoup
import glob
import re

liste_verbes = set()

paths = glob.glob("../corpus_annote/*")
nb_paths = len(paths)
compteur = 1
for path in paths:

    print(f"Traitement du fichier {compteur}/{nb_paths} ({path})")

    # Ouverture du fichier
    with open(path, "r", encoding = "utf8") as file:
        content = file.read()
        bs_content = BeautifulSoup(content, "xml")

    # extraction des verbes
    for ingredient in bs_content.find_all('ingredient'):
        liste_verbes.add(ingredient["action"])
        if len(re.findall(r"^-", ingredient["action"]))!=0:
            print(content)

    compteur += 1

liste_verbes = list(liste_verbes)
liste_verbes.sort()

with open("../ressources/action_culinaires.csv", "w") as file:
    for action in liste_verbes:
        file.write(action + "\n")
