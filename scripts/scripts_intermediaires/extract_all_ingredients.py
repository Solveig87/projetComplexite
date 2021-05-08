from bs4 import BeautifulSoup
import glob
import re

import spacy
from spacy import displacy
nlp = spacy.load('fr_core_news_lg')

ingredients = []
i=1
for file in glob.glob("../../corpus_train/*"):
    print(i)
    with open(file, "r") as file:
        content = file.read()
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
                ingredient = ingredient.split("-")
                liste_ingredients.extend([ingr for ingr in ingredient if ingr != ""])
            else:
                liste_ingredients.append(ingredient)


    """Formatage de la liste d'ingrédient (ingrédient : catégorie)"""
    quantite = re.compile(r"^(?:[0-9]+, ?[0-9]+|quelque|[0-9]+)(?: ?(?:pincée|cuillère(?: à (?:soupe|café))?|pot|verre|tranche|feuille|gramme|litre|[mcdk]?[gl]) de)?")

    for ingredient in liste_ingredients:
        try:
            ingredient = " ".join([token.lemma_ for token in nlp(ingredient)])
            if len(quantite.findall(ingredient)) == 1:
                quant = quantite.findall(ingredient)[0]
            else:
                quant = ""
            ingredient = re.sub(quant, "", ingredient).strip()
            ingredient = next(token.text for token in nlp(ingredient) if token.dep_ == "ROOT")
            if ingredient not in ingredients:
                ingredients.append(ingredient)
        except:
            print("Problème avec ", file)

    i+=1

ingredients.sort()
print(len(ingredients))
with open("../ressources/ingredients_all_recettes.txt", "w") as f:
    for ingredient in ingredients:
        f.write(ingredient+"\n")
