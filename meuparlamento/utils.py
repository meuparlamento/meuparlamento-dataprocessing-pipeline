# -*- coding: UTF-8 -*-
import re
from meuparlamento.comissions import comissions

def translate_comission_category(x): 
    r = "Outras" 

    for k in comissions.keys(): 
        if(x in comissions[k]): 
            return k 

    return r

def clean_quotes(text): 
    if("“" in text):        
        response = " ".join(re.findall('“([^"]*)”', text)).strip()
        if(len(response.split()) > 4):
            return response
    
    if('"' in text):        
        response = " ".join(re.findall('"([^"]*)"', text)).strip()
        if(len(response.split()) > 4):
            return response
        
    if(";" in text):
        return text.split(";")[0]
    
    return text

def parse_original_document_url(url):
    try:
        https_indexes = [ (i.start(), i.end()) for i in re.finditer('http+', url)]
        return url[https_indexes[-1][0]:]
    except:
        return url

#print(clean_quotes('Decreto-Lei n.º 60/2014, de 22 de abril, que “Estabelece um regime excecional destinado à seleção e recrutamento de pessoal docente para os estabelecimentos públicos de educação pré-escolar e dos ensinos básico e secundário na dependência do Ministério da Educação e Ciência”.'))
#print(clean_quotes('Recomenda ao Governo que promova o reforço da investigação no processo pós-colheita e conservação da "pêra rocha".'))
