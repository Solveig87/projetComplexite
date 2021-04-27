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
with open("../ressources/lexique_ingredients.json", "r") as file:
    lex = json.load(file)


"""Recherche et annotation des ingrédients dans le texte de préparation avec les attributs "action" et "quantité"
Lorsqu'un terme générique est trouvé, on recherche à quel(s) ingrédient(s) ils peuvent faire référence et on additionne les quantités correspondantes si plusieurs ingrédients concernés (exemple : si on a 4 fraises et 4 framboises dans la liste d'ingrédients, et que le mots "fruits" se trouvent dans le texte de préparation, ce dernier aura pour l'attribut "quantité" la valeur "4 + 4"
"""

prepa_annotee = []
for token in nlp(prepa):
    isIngr = False
    for categ, ingr in lex.items(): #on cherche chaque mot du texte dans le lexique
        if categ == token.lemma_ or token.lemma_ in ingr:
            #Recherche de l'action effectuée sur l'ingrédient
            gouv = token.head 
            while True:
                if gouv.pos_ == "VERB" or gouv.dep_ == "ROOT": #si on atteint la racine, on considère que ce doit être un verbe même si Spacy dit le contraire
                    break
                gouv = gouv.head
            #ajout des balises
            prepa_annotee.append("<ingredient action=\"" + gouv.lemma_ + "\">"+token.text+"</ingredient>")
            isIngr = True
            break
    if isIngr == False:
        prepa_annotee.append(token.text)
        
prepa_annotee = " ".join(prepa_annotee)

output = args.file[:-4]+"_annote.xml"
id = args.file[:-4].split("_")[-1]
intro_xml = "<?xml version=\"1.0\" encoding=\"utf-8\"?>\n<recette id=\""+id+"\">\n"
with open(output, "w") as f:
    f.write(intro_xml)
    f.write(prepa_annotee)
    f.write("\n</recette>")



