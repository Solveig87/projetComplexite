from bs4 import BeautifulSoup
from urllib.request import Request, urlopen
import re
from collections import defaultdict
import json

req = Request('http://www.les-calories.fr/', headers={'User-Agent': 'Mozilla/5.0'})
page = urlopen(req).read()

soup = BeautifulSoup(page, 'html.parser')

categories = soup.find_all("ul", attrs={'class':"arrows"})
lexique = defaultdict(list)

for categorie in categories:
    nom_categ = categorie.find("h3").getText()
    nom_categ = re.sub(r"\([^\)]+\)", "", nom_categ)
    nom_categ = nom_categ.lower().strip()
    for ingredient in categorie.find_all("div", attrs={'class':"description"}):
        ingredient = re.sub(r"\([^\)]+\)", "", ingredient.getText())
        ingredient = re.sub(r"(verre|bouteille|canette|dose).*", "", ingredient.lower())
        ingredient = ingredient.strip()
        if "ou" in ingredient:
            lexique[nom_categ].extend([ingredient for ingredient in ingredient.split(" ou ") if ingredient not in lexique[nom_categ]])
        elif ingredient not in lexique[nom_categ]:
            lexique[nom_categ].append(ingredient)

with open("ressources/lexique_ingredients.json", "w", encoding="utf8") as f:
    f.write(json.dumps(lexique, indent=4, ensure_ascii=False))

