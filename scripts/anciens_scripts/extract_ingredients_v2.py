import json
import re
from bs4 import BeautifulSoup
import argparse

import spacy
from spacy import displacy

# chargement du modèle spacy
nlp = spacy.load('fr_core_news_lg')

# Chargement du lexique et génération du lexique simplifié
with open("../ressources/lexique_ingredients.json", "r") as file:
    lex_original = json.load(file)
    lex_simplifie = {}
    for categorie, ingredients in lex_original.items():
        ingredients_simplifies = set()
        for ingr in ingredients:
            ingr_main = re.sub(r"\bfrais\b", "", ingr)
            ingr_main = next(token.lemma_ for token in nlp(ingr_main) if token.dep_ == "ROOT")
            ingredients_simplifies.add(ingr_main)
        lex_simplifie[categorie] = list(ingredients_simplifies)

def nettoyer_corps(texte):
    """
    Différents pré-traitements pour nettoyer/adapter le corps de la recette
    param : texte - string, le corps de la recette
    return : texte_clean - string, le corps de la recette nettoyé
    """
    texte_clean = texte.lower()
    texte_clean = re.sub(r"([\.,\)])", r"\1 ", texte_clean)
    texte_clean = re.sub(r"\(", " (", texte_clean)
    texte_clean = re.sub(r"([!;:\?/])", r" \1 ", texte_clean)
    texte_clean = re.sub(r"([0-9])([a-z])", r"\1 \2", texte_clean)
    texte_clean = re.sub(r"([a-z])([0-9])", r"\1 \2", texte_clean)
    texte_clean = re.sub(r"\s+", " ", texte_clean)

    return texte_clean

def is_ingr(token):
    """
    Vérifie si un token correspond à un ingrédient selon notre lexique d'ingrédients
    param : token_analyse - token Spacy, le token analysé
    return : Boolean - si le token est un ingrédient ou non
    """
    for categ, ingredients in lex_simplifie.items():
        if token.lemma_ in categ.split() or token.lemma_ in ingredients:
            return True

    return False

def get_action(token):
    """
    Fonction récursive pour trouver l'action à laquelle se rapporte un ingrédient
    param : token - token Spacy, token de l'ingrédient
    return : string, le lemme de l'action à laquelle l'ingrédient se rapporte
    """
    gouv = token.head
    if gouv.pos_ == "VERB" or gouv.dep_ == "ROOT":
        return gouv.lemma_
    return get_action(gouv)

"""Recherche et annotation des ingrédients dans le texte de préparation avec l'attribut 'action' """

def annoter_ingredients(recette, indice = 0, recette_annotee = []):
    """
    """
    if indice == len(recette):
        return " ".join(recette_annotee)

    token_courant = recette[indice]
    if is_ingr(token_courant):
        if recette[indice-1].text == "à" or (recette[indice-1].text == "de" and is_ingr(recette[indice-2])):
            recette_annotee.append(token_courant.text)
        else :
            #Recherche de l'action effectuée sur l'ingrédient
            action = get_action(token_courant)
            #ajout des balises
            recette_annotee.append(f"<ingredient action=\"{action}\">{token_courant.text}</ingredient>")
    else:
        recette_annotee.append(token_courant.text)

    return annoter_ingredients(recette, indice+1, recette_annotee)


parser = argparse.ArgumentParser(description="fichier")
parser.add_argument("-v", "--verbose", help="verbose mode", action="store_true")
parser.add_argument("file", help="input file")
args = parser.parse_args()

with open(file=args.file, encoding = "utf8") as file:
    content = file.readlines()
    content = "".join(content)
    bs_content = BeautifulSoup(content, "xml")

"""Extraction du texte détaillant les étapes de préparation"""
prepa = bs_content.find("preparation").getText()

# Premiers prétraitements sur le texte de préparation
prepa = nettoyer_corps(prepa)

# for ix, token in enumerate(doc_prepa):
#     if is_ingr(token):
#         # vérifier que le mot précédent n'est pas "à", ou que les deux mots précédents ne sont pas [ingredient]+de
#         if doc_prepa[ix-1].text == "à" or (doc_prepa[ix-1].text == "de" and is_ingr(doc_prepa[ix-2])):
#             pass
#         else :
#             #Recherche de l'action effectuée sur l'ingrédient
#             action = get_action(token)
#             #ajout des balises
#             prepa_annotee.append("<ingredient action=\"" + action + "\">"+token.text+"</ingredient>")
#             continue
#     prepa_annotee.append(token.text)
#
# prepa_annotee = " ".join(prepa_annotee)
tokens_recette = [token for token in nlp(prepa)]
prepa_annotee = annoter_ingredients(tokens_recette)

output = args.file[:-4]+"_annote.xml"
id = args.file[:-4].split("_")[-1]
intro_xml = "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n<recette id=\""+id+"\">\n"
with open(output, "w") as f:
    f.write(intro_xml)
    f.write(prepa_annotee)
    f.write("\n</recette>")
