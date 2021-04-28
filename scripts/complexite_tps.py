import json
import re
from bs4 import BeautifulSoup

import spacy
from spacy import displacy
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
float = re.compile(r"^[0-9]+ ?[-,] ?[0-9]+")
ingredients = []
for ingredient in bs_content.find_all('p'):
    ingredient = ingredient.getText()
    ingredient = re.sub(r"\([^\)]+\)", "", ingredient)
    ingredient = ingredient.strip()
    if not ingredient.startswith("Pour") and ingredient != "" :
        if "," in ingredient and len(float.findall(ingredient)) == 0:
            ingredient = ingredient.split(", ")
            ingredients.extend([ingr for ingr in ingredient if ingr != ""])
        elif "-" in ingredient and len(float.findall(ingredient)) == 0:
            ingredient = ingredient.split("- ")
            ingredients.extend([ingr for ingr in ingredient if ingr != ""])
        else:
            ingredients.append(ingredient)


"""Formatage de la liste d'ingrédient (ingrédient : quantité)"""
nombre = re.compile(r"^[0-9]+|^quelque|^[0-9]+ ?[-,] ?[0-9]+")
quantite = re.compile(r"^(?:[0-9]+|quelque|[0-9]+, ?[0-9]+) (?:pincée|cuillère à (?:soupe|café)|pot|verre|tranche|feuille|gramme|litre|[mcdk]?[gl]) de")

ingr_info = {}
for ingredient in ingredients:
    ingredient = " ".join([token.lemma_ for token in nlp(ingredient) if token.pos_ != "ADJ"])
    if len(quantite.findall(ingredient)) == 1:
        quant = quantite.findall(ingredient)[0]
    elif len(nombre.findall(ingredient)) == 1:
        quant = nombre.findall(ingredient)[0]
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
