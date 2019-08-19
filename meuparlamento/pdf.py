# -*- coding: UTF-8 -*-

from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import TextConverter
from pdfminer.layout import LAParams
from pdfminer.pdfpage import PDFPage
from six import StringIO

import subprocess
import os


MAX_FILESIZE_LIMIT = 500000

class PDFReader(object):

    #def __init__(self,file_path):
    #    self.file_path = file_path

    @staticmethod
    def pdf2summary( rscript, pdf_file):
        statinfo = os.stat(pdf_file)
        if(statinfo.st_size > MAX_FILESIZE_LIMIT):
            return None

        cmd = "Rscript {rscript} {pdf_file}".format(rscript=rscript, pdf_file=pdf_file)
        print(cmd)
        process = subprocess.Popen([cmd],stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        process.wait()

        output = process.communicate()
        output_str = output[0]
        
        res = output_str.decode("utf-8")
        res = res.replace("\\n","\n").replace("[1]","").strip()
        res = res[1:-1]

        print(res)
        return res
        
    @staticmethod
    def pdf2text(file):
        rsrcmgr = PDFResourceManager()
        retstr = StringIO()
        codec = 'utf-8'
        laparams = LAParams()
        device = TextConverter(rsrcmgr, retstr, codec=codec, laparams=laparams)
        #fp = open(self.file_path, 'rb')
        fp = file
        interpreter = PDFPageInterpreter(rsrcmgr, device)
        password = ""
        maxpages = 0
        caching = True
        pagenos=set()
        for page in PDFPage.get_pages(fp, pagenos, maxpages=maxpages, password=password,caching=caching, check_extractable=True):
            interpreter.process_page(page)
   #    fp.close()
        device.close()
        result = retstr.getvalue()
        retstr.close()

        result = result.replace("\\n","\n")

        return result     
            
            
#PDFReader().pdf2text(open("/home/arian/Developer/workspace/liaad/arquivopt2019/meuparlamento-dataprocessing/results/pdfs/40000.pdf", "rb"))