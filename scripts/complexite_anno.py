# complexite_anno.py - Solveig PODER, Camille REY
# calcule la complexité de la fonction d'annotation d'une recette en fonction de la taille de cette recette et produit un graphique
# argument 1 : le répertoire contenant tous les fichiers recettes à annoter

import argparse
import glob
from bs4 import BeautifulSoup
import time
import matplotlib.pyplot as plt
from annoter_recette import *
import statistics

def main():

    # --------------- récupération des arguments en ligne de commande --------------------
    parser = argparse.ArgumentParser(description = "fichier")
    parser.add_argument("-v", "--verbose", help = "verbose mode", action = "store_true")
    parser.add_argument("input_corpus", help = "directory for input corpus / répertoire du corpus d'entrée")
    parser.add_argument("output_directory", help = "directory for output diagram / répertoire du graphique de sortie")
    args = parser.parse_args()

    # --------------- traitement de tous les fichiers du corpus d'entrée -----------------

    paths = glob.glob(args.input_corpus+"/*")
    complexites = {}

    for path in paths:

        # Ouverture du fichier
        with open(path, "r", encoding = "utf8") as file:
            content = file.read()
            bs_content = BeautifulSoup(content, "xml")

        # Extraction du texte de préparation et calcul de sa longueur
        prepa = bs_content.find("preparation").getText()
        len_prepa = len([token for token in nlp(prepa)])

        # Calcul du temps d'annotation
        if len_prepa not in complexites.keys():
            complexites[len_prepa] = []
        start = time.perf_counter()
        tokens_prepa_annotes = annoter_recette(prepa)
        end = time.perf_counter()
        run_time = end - start
        complexites[len_prepa].append(run_time)

    complexites = {key:statistics.mean(value) for key, value in complexites.items()}
    x = [key for key, value in sorted(complexites.items())]
    y = [value for key, value in sorted(complexites.items())]
    
    plt.plot(x, y, color="blue")
    plt.xlabel("Longueur de la recette")
    plt.ylabel("Temps d'annotation")
    plt.title("Courbe de complexité en temps de la fonction d'annotation")
    plt.subplots_adjust(bottom=0.2)
    plt.savefig(args.output_directory+"/graphique_complexite.png")
    plt.close()

if __name__ == "__main__":
    main()