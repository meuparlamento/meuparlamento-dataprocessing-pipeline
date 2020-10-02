# -*- coding: UTF-8 -*-

import logging

import pymongo
from pymongo import MongoClient

logging.basicConfig(
    format='[%(name)s] %(levelname)s %(asctime)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.INFO)

logger = logging.getLogger(__name__)

class ProposalDAO(object):

    def __init__(self, config):
        mongo_uri = config.get('mongo_uri', 'mongodb://localhost:27017/')
        mongo_database = config.get('mongo_database', 'meuParlamento')

        self.db = MongoClient(mongo_uri)[mongo_database]
        self.db["proposals"].create_index([("BID", pymongo.DESCENDING),("url", pymongo.DESCENDING)],unique=True)

    def insert_proposal(self, doc):
        #check if has votes
        if("resultadoFinal" in doc.keys()):
            try:
                self.db["proposals"].insert_one(doc)
            except:
                logger.error("Failed to persist proposal")

from datetime import datetime

class Governo(object):

    def __init__(self, periodo, governo, oposicao, tipo_governo=None):
        self.periodo = periodo
        self.governo = governo
        self.oposicao = oposicao
        self.tipo_governo = tipo_governo

class GovernosPortugal(object):

    def __init__(self, *args, **kwargs):
        self.governos_pt = [
        Governo(periodo=(datetime(2002, 4, 6),      datetime(2004, 7, 17)),    governo=["PSD","CDS-PP"],    oposicao=["PS", "BE", "PCP", "PEV"]),
        Governo(periodo=(datetime(2004, 7, 18),     datetime(2005, 3, 12)),    governo=["PSD","CDS-PP"],    oposicao=["PS", "BE", "PCP", "PEV"]),
        Governo(periodo=(datetime(2005, 3, 13),     datetime(2009, 10, 26)),   governo=["PS"],              oposicao=["PSD", "CDS-PP", "BE", "PCP", "PEV"]),
        Governo(periodo=(datetime(2009, 10, 27),    datetime(2011, 6, 21)),    governo=["PS"],              oposicao=["PSD", "BE", "PCP", "PEV"]) ,
        Governo(periodo=(datetime(2011, 6, 22),     datetime(2015, 10, 30)),   governo=["PSD","CDS-PP"],    oposicao=["PS", "BE", "PCP", "PEV"]),
        Governo(periodo=(datetime(2015, 11, 1),     datetime(2015, 11, 26)),   governo=["PSD","CDS-PP"],    oposicao=["PS", "BE", "PCP", "PEV","PAN"]),
        Governo(periodo=(datetime(2015, 11, 27),    datetime.now()),           governo=["PS"],              oposicao=["PSD", "CDS-PP", "PAN", "BE", "PEV", "PCP"])
        ]

    def is_oposition(self, party, date_vote):
        
        governo_no_periodo = [gov for gov in self.governos_pt if gov.periodo[0] <= date_vote and date_vote <= gov.periodo[1]]
        if(len(governo_no_periodo) > 0):
            return party in governo_no_periodo[0].oposicao
        else:
            return False

    def is_governo(self, party, date_vote):
        governo_no_periodo = [gov for gov in self.governos_pt if gov.periodo[0] <= date_vote and date_vote <= gov.periodo[1]]
        if(len(governo_no_periodo) > 0):
            return party in governo_no_periodo[0].governo
        else:
            return False