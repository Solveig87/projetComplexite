# eval.py - Solveig PODER, Camille REY
# effectue l'évaluation de l'outil d'identification des ingrédients (précision + rappel) dans un fichier csv
# argument 1 : le répertoire contenant tous les fichiers annotés à évaluer
# argument 2 : le chemin du fichier de sortie (sans extension)

import re
import glob
from bs4 import BeautifulSoup
import argparse
from utils import *

def find_corresponding_ingredient(ingredient, categories, ingredients_found):
    """
    Pour un ingredient de la liste d'ingredients d'une recette, trouve l'élement
    qui lui correspond dans les ingrédients identifiés automatiquement (par notre programme)dans le corps de la recette
    Cet élément peut être l'ingrédient lui même ou la catégorie de l'ingrédient.
    param : ingredient - string, l'ingrédient évalué
            categories - liste, la liste des catégories possibles de l'ingrédient
    return : matching_ingredients - set, ensemble des ingrédients correspondants identifiés (ingrédient lui même et/ou catégories)
    """
    matching_ingredients = set()
    for ingr in ingredients_found:
        if ingredient == ingr or ingr in categories:
            matching_ingredients.add(ingr)
    return matching_ingredients

def evaluate(recette):
    """
    Evalue la performance (précision et rappel) de l'identifieur d'ingrédients sur une recette
    param : recette - string, la recette annotée en entier
    return : precision, rappel - float, la précision et le rappel de l'identifieur d'ingrédients
    """

    # Extraction des informations depuis la recette annotée
    bs_content = BeautifulSoup(recette, "xml")
    ingr_expected = get_ingredients_infos(bs_content)
    ingr_found = set([nlp(ingredient.getText().strip())[0].lemma_ for ingredient in  bs_content.find_all('ingredient')])
    operations = set([nlp(operation.getText().strip())[0].lemma_ for operation in  bs_content.find_all('operation')])

    # Si aucun ingrédient n'a été trouvé dans le texte, ou aucun ingrédient extrait de la liste d'ingrédients : on s'arrête là
    if len(ingr_found) == 0 or len(ingr_expected) == 0:
        return 0, 0

    vrais_positifs = set()
    faux_negatifs = set()
    for ingredient, infos in ingr_expected.items() :

        # Chercher si un ingrédient correspondant (et/ou sa catégorie) a été trouvé par notre programme
        elements_correspondants = find_corresponding_ingredient(ingredient.strip(), infos["catégories"], ingr_found)
        if len(elements_correspondants) != 0:
            vrais_positifs = vrais_positifs.union(elements_correspondants)

        # Prise en compte des cas particuliers "sel" et "poivre", souvent non explicité dans le corps
        # On regarde si notre programme a identifié les verbes saler/poivrer à la place
        elif ingredient == "sel":
            if "saler" in operations:
                continue
        elif ingredient == "poivre":
            if "poivrer" in operations:
                continue
        else :
            faux_negatifs.add(ingredient)

    # POUR OBSERVER EN DETAIL LE PROCESSUS D EVALUATION, DE-COMMENTER LES LIGNES SUIVANTES :
    # faux_positifs = [ingr for ingr in ingr_found if ingr not in vrais_positifs]
    # print(ingr_expected)
    # print(ingr_found)
    # print(vrais_positifs)
    # print(faux_positifs)
    # print(faux_negatifs)
    precision = len(vrais_positifs) / (len(ingr_found))
    rappel = len(vrais_positifs) / (len(vrais_positifs) + len(faux_negatifs))

    return precision, rappel

# --------------- récupération des arguments en ligne de commande --------------------
parser = argparse.ArgumentParser(description="fichier")
parser.add_argument("-v", "--verbose", help="verbose mode", action="store_true")
parser.add_argument("corpus", help="corpus annoté à partir duquel effectuer l'évaluation")
parser.add_argument("sortie", help="chemin du fichier (sans l'extension) dans lequel écrire la sortie csv")
args = parser.parse_args()

# ---------------- Traitement des fichiers du corpus à évaluer ------------------------

paths = glob.glob(args.corpus+"/*")
nb_paths = len(paths)
compteur = 1

evaluations = []
for path in paths:

    print(f"Traitement du fichier {compteur}/{nb_paths} ({path})")

    # Ouverture du fichier
    with open(path, "r", encoding = "utf8") as file:
        content = file.read()

    precision, rappel = evaluate(content)
    evaluations.append((path, str(precision), str(rappel)))

    compteur += 1

# Ecriture de la sortie
with open(args.sortie+".csv", "w") as file:
    file.write("Fichier\tprécision\trappel\n")
    for eval in evaluations:
        ligne = '\t'.join(eval)
        file.write(ligne+"\n")
    moyenne_prec = sum([float(eval[1]) for eval in evaluations]) / len(evaluations)
    moyenne_rap = sum([float(eval[2]) for eval in evaluations]) / len(evaluations)
    file.write(f"MOYENNES \t{moyenne_prec}\t{moyenne_rap}")
