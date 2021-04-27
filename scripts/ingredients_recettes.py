from bs4 import BeautifulSoup
import glob
import re

import spacy
from spacy import displacy
nlp = spacy.load('fr_core_news_md')

ingredients = []
for file in glob.glob("../projetComplexite/corpus/*"):
    with open(file, "r") as file:
        content = " ".join(file.readlines())
        doc = BeautifulSoup(content, "xml")

    """Extraction de la liste d'ingrédients"""
    float = re.compile(r"^[0-9]+ ?[-,] ?[0-9]+")
    liste_ingredients = []
    for ingredient in doc.find_all('p'):
        ingredient = ingredient.getText()
        ingredient = re.sub(r"\([^\)]+\)", "", ingredient)
        ingredient = ingredient.strip()
        if not ingredient.startswith("Pour") and ingredient != "" :
            if "," in ingredient and len(float.findall(ingredient)) == 0:
                ingredient = ingredient.split(", ")
                liste_ingredients.extend([ingr for ingr in ingredient if ingr != ""])
            elif "-" in ingredient and len(float.findall(ingredient)) == 0:
                ingredient = ingredient.split("- ")
                liste_ingredients.extend([ingr for ingr in ingredient if ingr != ""])
            else:
                liste_ingredients.append(ingredient)

        
    """Formatage de la liste d'ingrédient (ingrédient : catégorie)"""
    nombre = re.compile(r"^[0-9]+|^quelque|^[0-9]+, ?[0-9]+")
    quantite = re.compile(r"^(?:[0-9]+|quelque|[0-9]+, ?[0-9]+) (?:pincée|cuillère à (?:soupe|café)|pot|verre|tranche|feuille|gramme|litre|[mcdk]?[gl]) de")

    for ingredient in liste_ingredients:
        try:
            ingredient = " ".join([token.lemma_ for token in nlp(ingredient)])
            if len(quantite.findall(ingredient)) == 1:
                quant = quantite.findall(ingredient)[0]
            elif len(nombre.findall(ingredient)) == 1:
                quant = nombre.findall(ingredient)[0]
            else:
                quant = ""
            ingredient = re.sub(quant, "", ingredient)
            ingredient = ingredient.strip()
            ingredient = [token.text for token in nlp(ingredient) if token.dep_ == "ROOT"][0]
            if ingredient not in ingredients:
                ingredients.append(ingredient)
        except:
            print("Problème avec ", file)
            
ingredients.sort()
print(len(ingredients))
with open("../ressources/ingredients_recettes.txt", "w") as f:
    for ingredient in ingredients:
        f.write(ingredient+"\n")