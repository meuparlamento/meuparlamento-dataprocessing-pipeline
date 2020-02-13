from lxml import html
import requests
import lxml
from lxml import etree

import re

url = "http://app.parlamento.pt/BI2/"

"""
For testing:
https://arquivo.pt/wayback/20151209121800/http://app.parlamento.pt/BI2/
https://arquivo.pt/wayback/20140924015720/http://app.parlamento.pt/BI2/
"""

page = requests.get(url)

pg = re.sub("\<strong\>","",str(page.content, "utf8"))
pg = re.sub("\<\/strong\>","",pg)
tree = html.fromstring(pg)

ag_day = -1 # index for the day's agenda section

ag_day = tree.xpath("//table[contains(@title, 'Agenda do Dia')]")

tlbs = tree.xpath("//table[contains(@class, 'TabTitulBolInf2')]")

propostas = []
if ag_day:
    
    day_element = ag_day[0].getnext()

#    print(html.tostring(day_element))

    day_element2 = day_element.xpath(".//td[contains(@class,'ConteudoSubtitulo')]")

    day_txt = day_element2[0].text
    day_txt = re.sub("DIA","",day_txt)
    day_txt = re.sub("\(.*","",day_txt).strip() 

    """
    Attention.
    When years change, there is no indication of that in the text (See December 27th 2017 for example)
    """
    
    main_content = day_element.getnext()    
    aux = main_content.xpath(".//td[contains(@class,'ConteudoPlenarioTexto')]")
    
    for i in range(len(aux)):
        aux_p = aux[i].xpath(".//a")

        if aux_p:
            _title = aux_p[0].text
            _url = aux_p[0].get("href")
            _bid = None
            if("BID" in _url):
                _bid = _url.split("BID=")[1]
            
            propostas.append({"title":_title, "url":_url, "bid":_bid})        


# Request proposals details using Luigi task
from run_luigi import SimplifyDocumentSchema
from luigi import scheduler, worker

w = worker.Worker(scheduler=sch)

for proposta in propostas:
    task = SimplifyDocumentSchema(proposta["bid"])
    w.add(task)
    w.run()
