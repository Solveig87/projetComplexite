# utils.py - Solveig PODER, Camille REY
# ensemble de fonction utilisées par plusieurs autres scripts dans le projet

import json
import re
import spacy
from bs4 import BeautifulSoup
from collections import defaultdict

# chargement du modèle spacy
nlp = spacy.load('fr_core_news_lg')

# --------------- Chargement des lexiques --------------------------------------------

def simplifier_lex(lexique, lexique_simpl = {}):
    """
    Fonction récursive pour simplifier le lexique d'ingrédients (seulement le lemme du token gouvernant pour chaque ingrédient)
    param : lexique - dict, le lexique à simplifier
    return : lexique_simpl - dict, le lexique simplifié
    """

    if len(lexique) == 0:
        return lexique_simpl

    curr_key = list(lexique.keys())[0]

    ingredients_simplifies = set()
    for ingr in lexique[curr_key]:
        ingr_main = next(token.lemma_ for token in nlp(ingr) if token.dep_ == "ROOT")
        ingredients_simplifies.add(ingr_main)
    lexique_simpl[curr_key] = list(ingredients_simplifies)

    del lexique[curr_key]
    return simplifier_lex(lexique, lexique_simpl)

with open("../ressources/lexique_ingredients.json", "r") as file:
    lex_original = json.load(file)
    lexique_ingr = simplifier_lex(lex_original)

with open("../ressources/lexique_operations.csv", "r") as file:
    lines = file.readlines()
    lexique_ope = [line.strip().split("\t")[0] for line in lines]
    lexique_ope2 = lexique_ope + ["faire", "rendre", "laisser"]

# --------------- Fonctions --------------------------------------------
def _get_categorie(ingr, lexique, categories):
    """
    Fonction récursive - trouve la ou les catégories possibles pour un ingrédient
    param : ingr - string, l'ingrédient cherché
            lexique - le lexique dans lequel chercher
            categories - la liste des catégories trouvées
    return : categories - la liste des catégories possibles pour l'ingrédient
    """
    if len(lexique) == 0:
        if len(categories) == 0:
            categories.append("non définie")
        return categories

    curr_key = list(lexique.keys())[0]
    if ingr in curr_key.split() or ingr in lexique[curr_key]:
        categories.append(curr_key)
    del lexique[curr_key]

    return _get_categorie(ingr, lexique, categories)

def get_categorie(ingredient):
    """
    caller pour la fonction récursive _get_categorie()
    param : ingr - string, l'ingrédient dont on cherche les catégories
    return : liste des catégories possibles
    """
    categ = []
    return _get_categorie(ingredient, lexique_ingr.copy(), categ)

def get_ingredients_bruts(recette_xml):
    """
    Extrait les ingrédients (avec leur quantité) depuis une recette au format xml
    param : recette_xml - noeud BeautifulSoup, la recette entière
    return : liste_ingr - la liste des ingrédients
    """
    float = re.compile(r"^[0-9]+ ?[-,] ?[0-9]+")
    liste_ingr = []
    for ingredient in recette_xml.find_all('p'):
        ingredient = ingredient.getText()
        ingredient = re.sub(r"\([^\)]+\)", "", ingredient)
        ingredient = ingredient.strip()
        if ingredient.startswith("Pour"):
            ingredient = re.sub(r"Pour[^:]*", "", ingredient).strip()
        if ingredient != "" :
            if "," in ingredient and len(float.findall(ingredient)) == 0:
                ingredient = ingredient.split(", ")
                liste_ingr.extend([ingr for ingr in ingredient if ingr != ""])
            elif "-" in ingredient and len(float.findall(ingredient)) == 0:
                ingredient = ingredient.split("- ")
                liste_ingr.extend([ingr for ingr in ingredient if ingr != ""])
            else:
                liste_ingr.append(ingredient)
    return liste_ingr

def nettoyer_ingr(ingredient):
    """
    Nettoie le texte d'un ingrédient (enlève les adjectifs qui posent souvent problème avec l'analyse Spacy/ à cause de leur position)
    param : ingredient - string, l'ingredient à nettoyer
    return : ingredient_clean - string, l'ingrédient nettoyé
    """
    ingredient_clean = re.sub(r"\b(?:frais|beau|grand|petit|bel|sécher|sec|moyen|fumer|fumé|gros|bon|rassir|rassi|presque)\b", "", ingredient)
    ingredient_clean = re.sub(r"\s+", " ", ingredient_clean)
    ingredient_clean = re.sub(r"^un", "1", ingredient_clean)
    ingredient_clean = re.sub(r"1/2", "0,5", ingredient_clean).strip()
    return ingredient_clean

def get_ingredients_infos(recette_xml):
    """
    Extrait les ingrédients et leurs informations (quantité/catégorie) depuis la
    liste des ingrédients d'une recette et le lexique d'ingrédients
    param : recette_xml - noeud BeautifulSoup, la recette entière
    return : ingr_info - dict, les informations des ingrédients
    """

    ingredients = get_ingredients_bruts(recette_xml)

    quantite = re.compile(r"^(?:[0-9]+, ?[0-9]+|quelque|[0-9]+)(?: ?(?:pincée|demi|cuillère(?: à (?:soupe|café|thé))?|pot|verre|boite|boîte|sachet|branche|brin|filet|pavé|tranche|peu|feuille|gramme|kilogramme|milligrame|millilite|centilitre|litre|[mcdk]?[gl](?:r)?)(?: de)? )?")

    ingr_info = defaultdict(dict)
    for ingredient in ingredients:
        try :

            # nettoyer et lemmatiser le texte de l'ingrédient
            ingredient = ingredient.replace("sauce", "").lower()
            ingredient = " ".join([token.lemma_ for token in nlp(ingredient) if token.pos_ != "VERB"])
            ingredient = nettoyer_ingr(ingredient)

            # trouver la quantité si elle est précisée
            quant = quantite.findall(ingredient)
            if len(quant) == 1:
                quant = quant[0]
            else:
                quant = ""

            # isoler l'ingrédient
            ingredient = re.sub(quant, "", ingredient).strip()
            ingredient = [token.lemma_ for token in nlp(ingredient) if token.dep_ == "ROOT"][0]

            # nettoyer la quantité
            quant = re.sub(" de", "", quant)

            # ajout des informations
            if ingredient not in ingr_info.keys():
                ingr_info[ingredient]["quantité"] = quant.strip()
                ingr_info[ingredient]["catégories"] = get_categorie(ingredient)
            else:
                if quant:
                    ingr_info[ingredient]["quantité"] += "+"+quant.strip()
        except :
            pass

    return ingr_info
