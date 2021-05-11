import re
from bs4 import BeautifulSoup
import argparse
import glob
from utils import *
import numpy

# --------------- Chargement des lexiques, création tables équivalence----------------------

table_quantite = {}
with open("../ressources/conversion_quantite.txt", "r") as file:
    lignes = file.readlines()
    for ligne in lignes:
        unite, equivalent = ligne.strip().split("--")
        table_quantite[unite] = float(equivalent)

table_operations = {}

ope_recipient = []

with open("../ressources/lexique_operations.csv", "r") as file:
    lignes = file.readlines()
    for ligne in lignes:
        ligne = ligne.strip().split("\t")
        if len(ligne) == 2:
            table_operations[ligne[0]] = float(ligne[1])
        elif len(ligne) == 3:
            ope_recipient.append(ligne[0])

table_niveaux = {'Très facile': 1, 'Facile' : 2, 'Moyennement difficile' : 3, 'Difficile' :4}

categ_recipient = ["coquillage crustacés", "poisson", "viande", "volaille"]

# --------------- Fonctions pour calculer les complexités ---------------------------------

def convert_quantite(quantite):
    """
    """
    # si la quantité est vide
    if quantite == "":
        return 0.5

    # Extraction du nombre et de l'unité
    nombre = re.findall(r"^(?:[0-9]+, ?[0-9]+|quelque|[0-9]+)", quantite)[0]
    unite = re.sub(nombre, "", quantite).strip()

    # Conversion du nombre
    nombre = re.sub(r"\s+", "", nombre)
    nombre = nombre.replace(",", ".")
    nombre = nombre.replace("quelque", "5")
    nombre = float(nombre)

    # Si aucune unité précisée
    if unite == "":
        return nombre

    # Conversion de l'unité et calcul
    quantite_convertie = table_quantite[unite] * nombre
    return quantite_convertie

def calculer_quantite(quantite):
    """
    """
    quantite = quantite.replace(";", "+")
    quantites = quantite.split("+")

    quantite_finale = 0
    for quantite in quantites:
        quantite_finale += convert_quantite(quantite)

    return quantite_finale

def complexite_temps_ope(action):
    """
    """
    if action in table_operations.keys():
        return table_operations[action]
    return 1

def calculer_complexite_temps(recette):
    """
    """
    complexite_temps = 0

    # Extraction des opérations associées à un ingrédient, en tenant compte de la quantité de l'ingrédient
    for ingredient in recette.find_all('ingredient'):
        if ingredient.has_attr('action'):
            if ingredient.has_attr("quantite"):
                quantite = calculer_quantite(ingredient["quantite"])
            else :
                quantite = 0.5
            action = complexite_temps_ope(ingredient["action"])
            complexite_temps += action * quantite

    # Ajout des opérations sans ingrédients associés
    for operation in recette.find_all('operation'):
        if not(operation.has_attr("ingredients")):
            action = nlp(operation.getText().strip())[0].lemma_
            action = complexite_temps_ope(action)
            complexite_temps += action

    return complexite_temps

def calculer_complexite_espace(recette):
    """
    """
    complexite_espace = 0

    # Ajout des récipients de base pour les ingrédients
    ingr_info = get_ingredients_infos(recette)
    for ingredient, infos in ingr_info.items():
        if any(categ in categ_recipient for categ in infos["catégories"]):
            complexite_espace += 1

    # Ajout des récipients liés à des actions
    operations_noDoublon = set([nlp(operation.getText().strip())[0].lemma_ for operation in recette.find_all("operation")])
    for operation in operations_noDoublon:
        if operation in ope_recipient:
            complexite_espace += 1

    return complexite_espace

# --------------- récupération des arguments en ligne de commande --------------------
parser = argparse.ArgumentParser(description = "fichier")
parser.add_argument("-v", "--verbose", help = "verbose mode", action = "store_true")
parser.add_argument("corpus", help = "corpus annoté à partir duquel effectuer les analyses de complexité")
parser.add_argument("sortie", help = "chemin du fichier (sans l'extension) dans lequel écrire la sortie csv")
args = parser.parse_args()

# ---------------- Traitement des fichiers du corpus à évaluer ------------------------

informations_complexite = []

paths = glob.glob(args.corpus+"/*")
nb_paths = len(paths)
compteur = 1

for path in paths:

    print(f"Traitement du fichier {compteur}/{nb_paths} ({path})")

    # Ouverture du fichier
    with open(path, "r", encoding = "utf8") as file:
        content = file.read()
        recette = BeautifulSoup(content, "xml")

    # Calculs des complexités
    complexite_temps = calculer_complexite_temps(recette)
    complexite_espace = calculer_complexite_espace(recette)

    # Conversion du niveau de difficulté
    niveau = table_niveaux[recette.find("niveau").getText()]

    informations_complexite.append((path, complexite_temps, complexite_espace, niveau))

    compteur += 1

# Calcul coeffs correlation:
comp_temps = numpy.array([info[1] for info in informations_complexite])
comp_espace = numpy.array([info[2] for info in informations_complexite])
niveaux = numpy.array([info[3] for info in informations_complexite])

corr_temps_espace = numpy.corrcoef(comp_temps, comp_espace)[0, 1]
corr_temps_niveau = numpy.corrcoef(comp_temps, niveaux)[0, 1]
corr_espace_niveau = numpy.corrcoef(comp_espace, niveaux)[0, 1]

# Ecriture sortie
with open(args.sortie+".csv", "w") as file:
    file.write("Fichier\tComplexité en temps\tComplexité en espace\tNiveau difficulté\n")
    for info in informations_complexite:
        ligne = '\t'.join([str(cellule) for cellule in info])
        file.write(ligne+"\n")
    file.write(f"CORRELATION temps-niveau\t{corr_temps_niveau}\n")
    file.write(f"CORRELATION espace-niveau\t{corr_espace_niveau}\n")
    file.write(f"CORRELATION temps-espace\t{corr_temps_espace}\n")
