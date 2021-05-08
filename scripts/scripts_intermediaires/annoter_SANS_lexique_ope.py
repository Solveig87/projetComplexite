import json
import re
from bs4 import BeautifulSoup
import argparse
import glob
import sys

# Puisque le programme doit être écrit avec bcp de récursion, il faut gérer les cas de recettes longues avec plus de 1000 tokens à traiter
sys.setrecursionlimit(1500)

import spacy
from spacy import displacy

# chargement du modèle spacy
nlp = spacy.load('fr_core_news_lg')

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

def nettoyer_corps(texte):
    """
    Différents pré-traitements pour nettoyer/adapter le corps de la recette
    param : texte - string, le corps de la recette
    return : texte_clean - string, le corps de la recette nettoyé
    """
    texte_clean = texte.lower()
    texte_clean = re.sub(r"([\.,\)])", r"\1 ", texte_clean)
    texte_clean = re.sub(r"\(", " (", texte_clean)
    texte_clean = re.sub(r"[^a-zA-Z]-", ". ", texte_clean)
    texte_clean = re.sub("^-", "", texte_clean)
    texte_clean = re.sub(r"([!;:\?/])", r" \1 ", texte_clean)
    texte_clean = re.sub(r"([0-9])([a-z])", r"\1 \2", texte_clean)
    texte_clean = re.sub(r"([a-z])([0-9])", r"\1 \2", texte_clean)
    texte_clean = re.sub(r"\s+", " ", texte_clean)
    texte_clean = re.sub(r"^\s+", "", texte_clean)
    return texte_clean

def is_ingr(token):
    """
    Vérifie si un token correspond à un ingrédient selon notre lexique d'ingrédients
    param : token_analyse - token Spacy, le token analysé
    return : Boolean - si le token est un ingrédient ou non
    """
    for categ, ingredients in lexique.items():
        if token.lemma_ in categ.split() or token.lemma_ in ingredients:
            return True

    return False

def get_action(token):
    """
    Fonction récursive pour trouver l'action à laquelle se rapporte un ingrédient
    param : token - token Spacy, token de l'ingrédient
    return : token, le token Spacy de l'action à laquelle l'ingrédient se rapporte
    """
    gouv = token.head
    if gouv.pos_ == "VERB" or gouv.dep_ == "ROOT":
        return gouv
    return get_action(gouv)

def _annoter_ingredients(recette, indice, recette_annotee):
    """
    Fonction récursive pour annoter les ingrédients et les opérations culinaires
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
            #print(recette.index(action))
            #ajout des balises
            recette_annotee.append(f"<ingredient action=\"{action.lemma_}\">{token_courant.text}</ingredient>")
    else:
        recette_annotee.append(token_courant.text)

    return _annoter_ingredients(recette, indice+1, recette_annotee)

def annoter_ingredients(recette):
    """
    Helper fonction car les paramètres "par défaut" ne fonctionnent pas pour les récursives si on les
    appelle plusieurs fois au cours de l'exécution d'un script (problème de résultats qui s'écrivent par dessus les résultats précédents)
    Cette fonction évite de devoir explicitement passer "0" et "[]" en paramètres quand on appellera annoter_ingredients
    """
    return _annoter_ingredients(recette, 0, [])

# Chargement du lexique et génération du lexique simplifié
with open("../ressources/lexique_ingredients.json", "r") as file:
    lex_original = json.load(file)
    lexique = simplifier_lex(lex_original)

# récupération des arguments en ligne de commande
parser = argparse.ArgumentParser(description = "fichier")
parser.add_argument("-v", "--verbose", help = "verbose mode", action = "store_true")
parser.add_argument("input_corpus", help = "directory for input corpus / répertoire du corpus d'entrée")
parser.add_argument("output_corpus", help = "directory for output corpus / répertoire du corpus de sortie")
args = parser.parse_args()

paths = glob.glob(args.input_corpus+"/*")
nb_paths = len(paths)
compteur = 1
for path in paths:

    print(f"Traitement du fichier {compteur}/{nb_paths} ({path})")

    # Ouverture du fichier
    with open(path, "r", encoding = "utf8") as file:
        content = file.read()
        bs_content = BeautifulSoup(content, "xml")

    # Extraction et nettoyage du texte de la préparation
    prepa = bs_content.find("preparation").getText()
    prepa = nettoyer_corps(prepa)

    # Annotation
    tokens_recette = [token for token in nlp(prepa)]
    prepa_annotee = annoter_ingredients(tokens_recette)

    # Ecriture de la sortie
    file_name = path.split("/")[-1][:-4]
    id = file_name.split("_")[-1]
    output = args.output_corpus + "/" + file_name + "_annote.xml"
    with open(output, "w") as f:
        f.write(f"<?xml version=\"1.0\" encoding=\"utf-8\"?>\n<recette id=\"{id}\">\n")
        f.write(prepa_annotee)
        f.write("\n</recette>")

    compteur += 1
