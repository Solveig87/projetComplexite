from bs4 import BeautifulSoup
import glob
import re

import spacy
from spacy import displacy
nlp = spacy.load('fr_core_news_md')

verbs = []
for file in glob.glob("../corpus/*"):
    with open(file, "r") as file:
        content = " ".join(file.readlines())
        doc = BeautifulSoup(content, "xml")
        text = doc.find("preparation").getText()
        #Corrections des nombreux problèmes d'espaces manquants dans le corpus
        text = text.lower()
        text = re.sub(r"([\.,\)])", r"\1 ", text)
        text = re.sub(r"\(", " (", text)
        text = re.sub(r"([!;:\?/])", r" \1 ", text)
        text = re.sub(r"([0-9])([a-z])", r"\1 \2", text)
        text = re.sub(r"([a-z])([0-9])", r"\1 \2", text)
        text = re.sub(r"\s+", " ", text)
        for line in text.split("\n"):
            line = nlp(line)
            for token in line:
                lemma = re.sub(r"^[0-9]?-", "", token.lemma_)
                if token.pos_ == "VERB" and lemma not in verbs and len(lemma)>3:
                    verbs.append(lemma)
            
verbs.sort()
print(len(verbs))
with open("ressources/lex_verbs.txt", "w") as f:
    for verb in verbs:
        f.write(verb+"\n")

