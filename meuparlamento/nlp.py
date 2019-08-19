# -*- coding: UTF-8 -*-

import yake
import json

import re

from sumy.parsers.plaintext import PlaintextParser
from sumy.nlp.tokenizers import Tokenizer
from sumy.summarizers.lsa import LsaSummarizer as Summarizer
from sumy.nlp.stemmers import Stemmer
from sumy.utils import get_stop_words

# TODO refactor
LANGUAGE = "portuguese"

class ContentSummarizer(object):

    def __init__(self, limit_sentences=5):
        pass
        self.keyword_extractor = yake.KeywordExtractor(lan="pt", n=1, dedupLim=0.9, dedupFunc='seqm', windowsSize=1, top=10, features=None)
        self.limit_sentences = limit_sentences

    def compute(self, text):
        text = text.replace("\t"," ").replace("\f"," ").replace("\n"," ").strip()
        
        parser = PlaintextParser.from_string(text, Tokenizer(LANGUAGE))
        stemmer = Stemmer(LANGUAGE)
        summarizer = Summarizer(stemmer)
        summarizer.stop_words = get_stop_words(LANGUAGE)

        summ = " ".join([sentence._text for sentence in summarizer(parser.document, self.limit_sentences)])
        
        if(len(summ) > 0):           
            keywords = self.keyword_extractor.extract_keywords(summ)        
        else:
            keywords = self.keyword_extractor.extract_keywords(text)

        keywords = [kw[0] for kw in keywords]
      
        metadata = {
            "keywords" : keywords,
            "summary_orig" : summ,
            "summary": self.fix_summary(summ)
        }

        return metadata

    def fix_summary(self, input_summary):
        strSum = input_summary

        if "Grupo Parlamentar" in strSum:
            strSum_new = re.sub(" +", " ", strSum)
            strSum_new = re.sub("Email: \S+@\S+\.\S+", "", strSum_new)
            strSum_new = re.sub("Telefone:(\s|\d)+", "", strSum_new)
            strSum_new = re.sub('Fax:(\s|\d)+', "", strSum_new)
            strSum_new = re.sub('Assembleia da Rep.blica . Pal.cio de S\. Bento . 1249.068 Lisboa', "", strSum_new)
            strSum_new = re.sub('(ftp|http|https):\/\/[^ "]+', "", strSum_new)
            strSum_new = re.sub('Grupo Parlamentar do Bloco de Esquerda', "[...]", strSum_new)
            strSum_new = re.sub('(- )+', "", strSum_new)
            strSum_new = re.sub('(– )+', "", strSum_new)
            strSum_new = re.sub('PARTIDO COMUNISTA PORTUGU.S', "[...]", strSum_new)
            strSum_new = re.sub('Grupo Parlamentar do PCP', "[...]", strSum_new)
            strSum_new = re.sub('Grupo Parlamentar do Partido Social Democrata', "[...]", strSum_new)
            strSum_new = re.sub('Grupo Parlamentar do PSD', "[...]", strSum_new)
            strSum_new = re.sub('Os Deputados, .+$', "[...]", strSum_new)
            strSum_new = re.sub('Grupo Parlamentar Os Verdes', "[...]", strSum_new)
            strSum_new = re.sub('Grupo Parlamentar do Partido Socialista', "[...]", strSum_new)
            strSum_new = re.sub('Grupo Parlamentar do PS', "[...]", strSum_new)
            strSum_new = re.sub('Grupo Parlamentar do CDS.PP', "[...]", strSum_new)
            strSum_new = re.sub('Bloco de Esquerda', "[...]", strSum_new)
            strSum_new = re.sub('PS, PSD e CDS', "[...]", strSum_new)
            strSum_new = re.sub('PSD\/CDS', "[...]", strSum_new)
            strSum_new = re.sub('Grupo Parlamentar', "[...]", strSum_new)
            strSum_new = re.sub('PCP', "[...]", strSum_new)
            strSum_new = re.sub('CDS.PP', "[...]", strSum_new)
            strSum_new = re.sub('(Os|As) (Deputados|Deputadas) [A-ZÁÀÃÂÉÈÊÍÌÎÓÒÕÔÚÙÛÇ’\-\s]+$', "[...]", strSum_new)
            strSum_new = re.sub('(\(.+\))\s+(\(.+\))', "[...]", strSum_new)
            strSum_new = re.sub(" +", " ", strSum_new)
            strSum = strSum_new
        
        return strSum