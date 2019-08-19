# -*- coding: UTF-8 -*-
from meuparlamento.utils import clean_quotes, parse_original_document_url
from meuparlamento.models import  GovernosPortugal
from datetime import datetime 

class ReadabilityScore(object):

    def compute(self, row):
        if not(row):
            return

        readability_score = 0
        governosPortugal = GovernosPortugal()

        is_governo = False
        is_oposition = False
        
        if("dataVotacao" not in row.keys()):
            return

        voteDate = datetime.utcfromtimestamp(row["dataVotacao"]["$date"]/1000)
        
        for party in row["proposedBy"].split(","):
            if(governosPortugal.is_governo(party,voteDate)):
                is_governo = True
                
        for party in row["proposedBy"].split(","):
            if(governosPortugal.is_oposition(party,voteDate)):
                is_oposition = True
    
        clean_title = clean_quotes(row["title"])
        
        num_chars = len(clean_title)
        num_tokens =  len(clean_title.split())
        
        if(num_tokens <= 3):
            readability_score -=1
            
        if("Lei n.º" in clean_title):
            readability_score -=1
            
        if("Portaria nº" in clean_title):
            readability_score -=1
            
        if("República n.º" in clean_title):
            readability_score -=1
        
        if(num_chars >= 250):
            readability_score -=1
        
        metadata = {
            "title": clean_title,
            "anoVotacao": row["anoVotacao"],
            "proposedBy": row["proposedBy"],
            "num_chars": num_chars,
            "num_tokens": num_tokens,
            "is_governo": is_governo,
            "is_oposition": is_oposition,
            "readability_score":readability_score,
        }
        
    #     compute original document url
    #    if("arquivo.pt" in row["pdfLink"]):
        #    metadata["pdfLink"] = parse_original_document_url(row["pdfLink"])

    #    row["metadata"] = metadata
    #    return row
        return metadata

