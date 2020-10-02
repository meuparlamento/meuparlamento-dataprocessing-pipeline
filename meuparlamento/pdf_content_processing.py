from io import StringIO

from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfdocument import PDFDocument
from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.pdfpage import PDFPage
from pdfminer.pdfparser import PDFParser

import re
import nltk.data

sent_detector = nltk.data.load("tokenizers/punkt/portuguese.pickle")

PLACEHOLDER_PATTERNS = [
    (r"Assembleia da República.+",""),
    (r"Projecto.+",""),
    (r"PROJETO",""),
    (r"PROJECTO",""),
    (r"Email: \\S+@\\S+\\.\\S+",""),
    (r"Telefone:(\\s|\\d)+",""),
    (r"Fax:(\\s|\\d)+",""),
    (r"Assembleia da Rep.blica . Pal.acio de S\\. Bento. 1249.068 Lisboa",""),
    (r"Assembleia da República, \\d+.+$",""),

    (r'(ftp|http|https):\\/\\/[^ "]',""),
    (r"Pal.cio de São Bento.+","[...]"),
    (r"Grupo Parlamentar do Bloco de Esquerda","[...]"),
    (r"(- )+",""),
    (r"PARTIDO COMUNISTA PORTUGU.S","[...]"),
    (r"Partido socialista","[...]"),
    (r"Grupo Parlamentar do PCP","[...]"),
    (r"Grupo Parlamentar do Partido Social Democrata","[...]"),
    (r"Grupo Parlamentar do PSD","[...]"),
    (r"Os Deputados, .+$","[...]"),
    (r"Grupo Parlamentar Os Verdes","[...]"),
    (r"Grupo Parlamentar do Partido Socialista","[...]"),
    (r"Grupo Parlamentar do PSD","[...]"),
    (r"Grupo Parlamentar do CDS.PS","[...]"),
    (r"Bloco de Esquerda","[...]"),
    (r"PS, PSD e CDS","[...]"),
    (r"PSD\\/CDS.PP","[...]"),
    (r"Grupo Parlamentar","[...]"),
    (r"Governo PSD-CDS","[...]"),
    (r"Governo PS","[...]"),
    (r"PSD","[...]"),
    (r"PCP",""),
    (r"PS","[...]"),
    (r"CDS.PP","[...]"),
    (r"CDS","[...]"),
    (r"PEV","[...]"),
    (r"PAN","[...]"),

    (r"Partido Ecologista Os (V|v)erdes (PEV)","[...]"),
    (r"Partido Ecologista Os (V|v)erdes","[...]"),
    (r"Os Verdes","[...]"),
    (r"(Os|As) (Deputados|Deputadas) [A-ZÁÀÃÂÉÈÊÎÍÓÔÚÛÇ'\\-\\s]+$","[...]"),
    (r"PAN","[...]"),

    (r"^[...]\\s",""),
    (r"^ẃ","-"),
    (r"^\\d(\\s|\\.)+",""),
]


def preprocess_pdf_content(pdf_filepath):
    output_string = StringIO()
    with open(pdf_filepath, "rb") as in_file:
        parser = PDFParser(in_file)
        doc = PDFDocument(parser)
        rsrcmgr = PDFResourceManager()
        device = TextConverter(rsrcmgr, output_string, laparams=LAParams())
        interpreter = PDFPageInterpreter(rsrcmgr, device)

        for page in PDFPage.create_pages(doc):
            interpreter.process_page(page)

    return output_string.getvalue()

def process_pdf_content(pdf_content):
    document = pdf_content.replace("\n\n","\n")
    document_lines = []

    for line in document.split("\n"):
        if line.title().startswith("Grupo Parlamentar") or line.upper().startswith("PROJETO RESOLUÇÃO"):
            continue
        else:
            document_lines.append(line)

    return " ".join(document_lines)

def text_placeholder(rp, _text):
    return re.sub(rp[0],rp[1],_text)

def fit_text_placeholders(_text):
    result = _text
    for rp in PLACEHOLDER_PATTERNS:
        result = text_placeholder(rp, result)

    return result

def set_text_placeholders(_doc):
    lines = sent_detector.tokenize(_doc.strip())

    new_doc = []
    for line in lines:
        preprocessed_line = fit_text_placeholders(line)

        new_doc.append(preprocessed_line)
    
    return new_doc

def extract_pdf_main_content(filepath):
    pdf_content = preprocess_pdf_content(filepath)
    pdf_content = process_pdf_content(pdf_content)
    pdf_content = set_text_placeholders(pdf_content)

    MAX_SENTENCES = 3

    return " ".join(pdf_content[0:MAX_SENTENCES])
