import json
import re
from bs4 import BeautifulSoup
import spacy
from spacy import displacy
from .utils import *
from collections import defaultdict
# chargement du modèle spacy
nlp = spacy.load('fr_core_news_md')

import argparse
parser = argparse.ArgumentParser(description="fichier")
parser.add_argument("-v", "--verbose", help="verbose mode", action="store_true")
parser.add_argument("file", help="input file")
args = parser.parse_args()

with open(file=args.file, encoding = "utf8") as file:
    content = file.readlines()
    content = "".join(content)
    bs_content = BeautifulSoup(content, "xml")

"""Extraction de la liste d'ingrédients"""
ingredients = get_ingredients_bruts(bs_content)

"""Formatage de la liste d'ingrédient (ingrédient : quantité)"""

quantite = re.compile(r"^(?:[0-9]+, ?[0-9]+|quelque|[0-9]+)(?: ?(?:pincée|demi|cuillère(?: à (?:soupe|café))?|pot|verre|tranche|feuille|gramme|kilogramme|litre|[mcdk]?[gl](?:r)?)(?: de)? )?")

ingr_info = {}
for ingredient in ingredients:
    ingredient = " ".join([token.lemma_ for token in nlp(ingredient)])
    ingredient = re.sub(r"^un", "1", ingredient)
    quantite = quantite.findall(ingredient)
    if len(quantite) == 1:
        quant = quantite[0]
    else:
        quant = ""
    ingredient = re.sub(quant, "", ingredient)
    ingredient = ingredient.strip()
    ingredient = [token.text for token in nlp(ingredient) if token.dep_ == "ROOT"][0]
    quant = re.sub(" de", "", quant)
    ingr_info[ingredient] = quant.strip()

print(ingr_info)


"""Chargement du texte de la recette annotée et récupération des actions avec le nombre d'ingrédients pour calcul complexité"""
recette_annotee_path = args.file[:-4]+"_annote.xml"
ingredients = {}
with open(recette_annotee_path, "r") as f:
    content = f.readlines()
    content = "".join(content)
    bs_content = BeautifulSoup(content, "xml")
for ingredient in bs_content.find_all('ingredient'):
    ingredients[[token.lemma_ for token in nlp(ingredient.getText())][0]]= ingredient['action']

print(ingredients)

from collections import Counter

actions = Counter()
nb = re.compile(r"^[0-9]+|^[0-9]+ ?[-,] ?[0-9]+")

for ingredient, action in ingredients.items():
    if ingredient in ingr_info.keys():
        nb_ingr = ingr_info[ingredient]
    else:
        nb_ingr = 1
    try:
        nb_ingr = int(nb_ingr)
    except:
        if len(nb.findall(nb_ingr)) > 0:
            nb_ingr = nb.findall(nb_ingr)[0]
            nb_ingr = re.sub(r" ?, ?", "\.", nb_ingr)
            if "-" in nb_ingr:
                nb_ingr = nb_ingr.split("-")[0]
            nb_ingr = int(nb_ingr)
        else:
            nb_ingr = 1

    actions[action] += nb_ingr

print(actions)

complexite = len(actions)/sum(actions.values())

print(f"La complexité de cette recette est de {complexite}.")
