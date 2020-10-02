from lxml import html
import requests
import lxml
from lxml import etree
import os
import re

os.system("./set_env.sh")

print(os.environ)
# Last entries
url = "https://www.parlamento.pt/Paginas/UltimasIniciativasEntradas.aspx"

page = requests.get(url)
pg = re.sub(b"\<strong\>","",page.content)
pg = re.sub(b"\<\/strong\>","",pg)
tree = html.fromstring(pg)

entries = tree.xpath(".//a[contains(@title, 'Detalhe de Iniciativa')]")

# 
from run_luigi import SimplifyDocumentSchema, ProposalDatabasePersistence
from luigi import scheduler, worker

for entry in entries:
    hyperlink = entry.get("href")
    bid = int(re.sub(".+\?BID=","",hyperlink))
    print(bid)

    # Request proposals details using Luigi task

    w = worker.Worker()

    # for proposta in propostas:
    task = SimplifyDocumentSchema(bid)
    w.add(task)
    w.run()

    task = ProposalDatabasePersistence(bid)
    w.add(task)
    w.run()
    