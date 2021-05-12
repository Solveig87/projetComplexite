# annoter_recette.py - Solveig PODER, Camille REY
# annote des recettes XML avec les informations : ingrédient (action, quantité) et opérations (ingrédients)
# argument 1 : le répertoire contenant tous les fichiers recettes à annoter
# argument 2 : le répertoire de sortie

import json
import re
from bs4 import BeautifulSoup
import argparse
import glob
import sys
from collections import defaultdict
from utils import *

# Puisque le programme doit être écrit avec bcp de récursion, il faut gérer les cas de recettes longues avec plus de 1000 tokens à traiter
sys.setrecursionlimit(1500)

# --------------- Classes et fonctions pour annoter ---------------------------------

class TokenAnnote():
    """
    Classe qui définit un token de recette enrichi d'annotations
    """
    def __init__(self, token_spacy):
        self.forme = token_spacy.text
        self.lemme = token_spacy.lemma_
        self.etiquette = ""
        self.attributs = defaultdict(list)

    def to_str(self):
        """
        Convertir un token annoté en un format balisé
        """
        token_str = ""
        if self.etiquette :
            attributs = ""
            for attrib, valeurs in self.attributs.items():
                attributs += f" {attrib}=\"{';'.join(valeurs)}\""
            token_str = f"<{self.etiquette}{attributs}> {self.forme} </{self.etiquette}>"
        else :
            token_str = self.forme
        return token_str

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
    texte_clean = re.sub(r"\\", "/", texte_clean)
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
    for categ, ingredients in lexique_ingr.items():
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

def _annoter_recette(tokens_spacy, indice, tokens_annotes):
    """
    Fonction récursive pour annoter les ingrédients et les opérations culinaires
    """
    if indice == len(tokens_spacy):
        return tokens_annotes

    token_courant = tokens_spacy[indice]
    if is_ingr(token_courant):
        # évitez d'annoter "riz" dans "galette de riz", ou "soupe" dans "cuillère à soupe"... tout en annotant "crème" dans "un peu de crème", "le pot de crème"...
        if tokens_annotes[indice-1].etiquette == "ingredient" or tokens_spacy[indice-1].text == "à" or (tokens_spacy[indice-1].lemma_ == "de" and tokens_annotes[indice-2].etiquette == "ingredient"):
            pass
        else :
            # annoter l'ingrédient
            tokens_annotes[indice].etiquette = "ingredient"

            # Recherche de l'action effectuée sur l'ingrédient
            action = get_action(token_courant)
            # si cette action est bien une opération culinaire
            if action.lemma_ in lexique_ope2:
                tokens_annotes[indice].attributs["action"].append(action.lemma_)

                # annoter l'opération correspondant à cet ingrédient
                gouv = tokens_spacy.index(action)
                tokens_annotes[gouv].etiquette = "operation"
                tokens_annotes[gouv].attributs["ingredients"].append(token_courant.text)

    elif token_courant.lemma_ in lexique_ope:
        # annoter l'opération
        tokens_annotes[indice].etiquette = "operation"

    return _annoter_recette(tokens_spacy, indice+1, tokens_annotes)

def annoter_recette(recette):
    """
    Fonction pour annoter les tokens d'une recette (ingredients + opérations culinaires)
    --> fait appel à la fonction récursive _annoter_recette pour annoter une recette
    param : recette - string, le texte de la recette
    return : liste d'objets TokenAnnote, les tokens annotés de la recette
    """
    tokens_spacy_recette = [token for token in nlp(nettoyer_corps(recette))]
    tokens_annotes = [TokenAnnote(token) for token in tokens_spacy_recette]
    return _annoter_recette(tokens_spacy_recette, 0, tokens_annotes)

def annoter_quantites(recette, tokens_annotes):
    """
    Enrichit les tokens annotés d'informations de quantité grâce à la correspondance
    avec les informations de la liste d'ingrédients
    param : recette - noeud BeautifulSoup, la recette entière
        tokens_annotes - liste d'objets TokenAnnote, la liste des tokens déjà annotés de la recette
    """
    ingredients_info = get_ingredients_infos(recette)
    for token in tokens_annotes:
        if token.etiquette == "ingredient":
            if token.lemme in ingredients_info.keys():
                token.attributs["quantite"].append(ingredients_info[token.lemme]["quantité"])
            else:
                for ingredient, infos in ingredients_info.items():
                    if any(token.lemme in categ.split() for categ in infos["catégories"]):
                        token.attributs["quantite"].append(infos["quantité"])
def main():
    # --------------- récupération des arguments en ligne de commande --------------------
    parser = argparse.ArgumentParser(description = "fichier")
    parser.add_argument("-v", "--verbose", help = "verbose mode", action = "store_true")
    parser.add_argument("input_corpus", help = "directory for input corpus / répertoire du corpus d'entrée")
    parser.add_argument("output_corpus", help = "directory for output corpus / répertoire du corpus de sortie")
    args = parser.parse_args()

    # --------------- traitement de tous les fichiers du corpus d'entrée -----------------

    paths = glob.glob(args.input_corpus+"/*")
    nb_paths = len(paths)
    compteur = 1

    for path in paths:

        print(f"Traitement du fichier {compteur}/{nb_paths} ({path})")

        # Ouverture du fichier
        with open(path, "r", encoding = "utf8") as file:
            content = file.read()
            bs_content = BeautifulSoup(content, "xml")

        # Extraction du texte de préparation
        prepa = bs_content.find("preparation").getText()

        # Annotation ingrédients+opérations (grâce aux lexiques)
        tokens_prepa_annotes = annoter_recette(prepa)
        # Ajout des annotations de quantité (grâce à la liste d'ingrédients)
        annoter_quantites(bs_content, tokens_prepa_annotes)
        # conversion en string
        prepa_annotee = " ".join([token.to_str() for token in tokens_prepa_annotes])

        # Ecriture de la sortie
        file_name = path.split("/")[-1][:-4]
        output = args.output_corpus + "/" + file_name + "_annote.xml"
        with open(output, "w") as f:
            new_content = re.sub(r"<preparation>.*</preparation>", f"<preparation>\n{prepa_annotee}\n</preparation>", str(bs_content), flags = re.DOTALL)
            f.write(new_content)

        compteur += 1

if __name__ == "__main__":
    main()
