import json
import re
from bs4 import BeautifulSoup
import argparse

import spacy
from spacy import displacy
nlp = spacy.load('fr_core_news_md')

parser = argparse.ArgumentParser(description="fichier")
parser.add_argument("-v", "--verbose", help="verbose mode", action="store_true")
parser.add_argument("file", help="input file")
args = parser.parse_args()

with open(file=args.file, encoding = "utf8") as file:
    content = file.readlines()
    content = "".join(content)
    bs_content = BeautifulSoup(content, "xml")
    
"""Extraction de la liste d'ingrédients"""
ingredients = []
for ingredient in bs_content.find_all('p'):
    ingredient = ingredient.getText()
    if "," in ingredient:
        ingredient = ingredient.split(", ")
        ingredients.extend(ingredient)
    else:
        ingredients.append(ingredient)

"""Chargement du lexique"""
with open("../ressources/lexique_ingredients.json", "r") as file:
    lex = json.load(file)
    
"""Formatage de la liste d'ingrédient (ingrédient : catégorie)"""
nombre = re.compile(r"^[0-9]+|quelque")
quantite = re.compile(r"^(?:[0-9]+|quelque) (?:pincée|cuillère à (?:soupe|café)|pot|verre|tranche|feuille|gramme|litre|[mcdk]?[gl]) de")

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
    ingr_info[ingredient] = "NA" 
    for categ, ingrs in lex.items():
        for ingr in ingrs:
            ingr = [token.lemma_ for token in nlp(ingr) if token.dep_ == "ROOT"][0]
            if ingr == ingredient: #implémenter levenshtein ?
                ingr_info[ingredient] = categ
                break


"""Chargement du texte de la recette annotée et récupération de la liste d'ingrédients trouvés pour comparaison avec liste initiale"""
recette_annotee_path = args.file[:-4]+"_annote.xml"
ingredients = []
with open(recette_annotee_path, "r") as f:
    content = f.readlines()
    content = "".join(content)
    bs_content = BeautifulSoup(content, "xml")
for ingredient in bs_content.find_all('ingredient'):
    ingredients.extend([token.lemma_ for token in nlp(ingredient.getText())])


"""Calcul rappel"""
trouves = 0
for ingr, categ in ingr_info.items():
    if ingr in ingredients or categ in ingredients:
        trouves+=1
rappel = trouves/len(ingr_info)

"""Calcul precision"""
corrects = 0
for ingredient in ingredients:
    if ingredient in ingr_info.keys() or ingredient in ingr_info.values():
        corrects += 1
precision = corrects/len(ingredients)

fmesure = (2*precision*rappel)/(precision+rappel)

id = args.file[:-4].split("_")[-1]
print(f"Recette {id} : \n PRECISION : {precision} / RAPPEL : {rappel} / F-MESURE : {fmesure}")