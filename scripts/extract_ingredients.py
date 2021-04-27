import json
import re
from bs4 import BeautifulSoup

import spacy
from spacy import displacy
nlp = spacy.load('fr_core_news_md')

with open("../corpus/recette_400.xml", "r") as file:
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

"""Extraction du texte détaillant les étapes de préparation"""
prepa = bs_content.find("preparation").getText()
#Qqs prétraitements (bcp d'espaces manquants dans le corpus)
prepa = prepa.lower()
prepa = re.sub(r"([\.,\)])", r"\1 ", prepa)
prepa = re.sub(r"\(", " (", prepa)
prepa = re.sub(r"([!;:\?/])", r" \1 ", prepa)
prepa = re.sub(r"([0-9])([a-z])", r"\1 \2", prepa)
prepa = re.sub(r"([a-z])([0-9])", r"\1 \2", prepa)
prepa = re.sub(r"\s+", " ", prepa)
#print(prepa)


"""Chargement du lexique"""
with open("ressources/lexique_ingredients.json", "r") as file:
    lex = json.load(file)


"""Formatage de la liste d'ingrédient (ingrédient, quantité, catégorie)"""
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
    quant = re.sub(" de", "", quant)
    ingr_info[ingredient] = {} 
    ingr_info[ingredient]["quantité"] = quant.strip()
    for categ, ingrs in lex.items():
        if "catégorie" in ingr_info[ingredient].keys():
            break
        for ingr in ingrs:
            ingr = [token.lemma_ for token in nlp(ingr) if token.dep_ == "ROOT"][0]
            if ingr == ingredient: #implémenter levenshtein ?
                ingr_info[ingredient]["catégorie"] = categ
                break
    if not "catégorie" in ingr_info[ingredient].keys():
        ingr_info[ingredient]["catégorie"] = "inconnue"

        
print(ingr_info)

"""Recherche et annotation des ingrédients dans le texte de préparation avec les attributs "action" et "quantité"
Lorsqu'un terme générique est trouvé, on recherche à quel(s) ingrédient(s) ils peuvent faire référence et on additionne les quantités correspondantes si plusieurs ingrédients concernés (exemple : si on a 4 fraises et 4 framboises dans la liste d'ingrédients, et que le mots "fruits" se trouvent dans le texte de préparation, ce dernier aura pour l'attribut "quantité" la valeur "4 + 4"
"""

trouve = []
prepa_annotee = []
for token in nlp(prepa):
    isIngr = False
    for ingr, infos in ingr_info.items(): #on cherche chaque mot du texte dans la liste des ingrédients (nom ou catégorie) obtenue ci-dessus
        if ingr == token.lemma_ or token.lemma_ in infos["catégorie"].split():
            #Recherche de l'action effectuée sur l'ingrédient
            gouv = token.head 
            while True:
                if gouv.pos_ == "VERB" or gouv.dep_ == "ROOT": #si on atteint la racine, on considère que ce doit être un verbe même si Spacy dit le contraire
                    break
                gouv = gouv.head
            #ajout des balises
            if ingr == token.lemma_:
                prepa_annotee.append("<ingredient action=\"" + gouv.lemma_ + "\" quantite=\"" + infos["quantité"] + "\">"+token.text+"</ingredient>")
            elif token.lemma_ in infos["catégorie"].split():
                ingredients = [ingredient for ingredient in ingr_info.keys() if ingr_info[ingredient]["catégorie"] == infos["catégorie"]]
                quantite = " + ".join([ingr_info[ingredient]["quantité"] for ingredient in ingredients])
                prepa_annotee.append("<groupe_ingredients action=\"" + gouv.lemma_ + "quantite=\"" + quantite + "\">"+token.text+"</groupe_ingredients>")
            trouve.append(ingr)
            isIngr = True
            break
    if isIngr == False:
        prepa_annotee.append(token.text)
        
prepa_annotee = " ".join(prepa_annotee)

nontrouve = 0
for ingr in ingr_info:
    if ingr not in trouve:
        nontrouve+=1
        
print(f"{nontrouve} ingrédients n'ont pas été trouvés sur {len(ingr_info)}")
        
with open("sorties/recette_400_annotee.xml", "w") as f:
    f.write("<?xml version=\"1.0\" encoding=\"utf-8\"?>\n<recette id=\"400\">\n")
    f.write(prepa_annotee)
    f.write("\n</recette>")



