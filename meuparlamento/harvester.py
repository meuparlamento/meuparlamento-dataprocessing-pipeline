# -*- coding: UTF-8 -*-

from lxml import html
import requests
from datetime import datetime
from meuparlamento.utils import  parse_original_document_url
from urllib.parse import urlparse
import re
import logging
logger = logging.getLogger(__name__)

class PortugueseParlamentProposalsHarvester(object):
    
    def __init__(self, config):
        self.config = config

    def _handle_fetch_proposal_response(self, response):
        print("_handle_fetch_proposal_response")
        print("response.status_code",response.status_code)
        print("response.url",response.url)
        # if(response.status_code == 200):

        # print("response.content",response.content)

        proposal = self._parse_html(response.content)


        if(proposal):
            # set origin (arquivo.pt | parlamento.pt)
            proposal["source_domain"] = urlparse(response.url).netloc
            
            proposal["url"] = response.url
            proposal["BID"] = response.request.path_url.split("=")[1]

            # TODO refactor this
            if("arquivo.pt" in proposal["pdfLink"]):
                proposal["pdfLink"] = parse_original_document_url(proposal["pdfLink"])

            return proposal
        else:
            return None
                
    def fetch_proposal(self, bid):
        proposal_url = self.config.proposal_url_template + str(bid)

        logger.info(proposal_url)
        
        response = requests.get(proposal_url)
        if(response.status_code == 200):
            return self._handle_fetch_proposal_response(response)

        else:
            logger.info("Failed request. Try web archive")
            logger.info(proposal_url)
            proposal_url =  "{webarchive_url_replay}/{url}".format(webarchive_url_replay=self.config.webarchive_url_replay,
                                                                   url=proposal_url)
            response = requests.get(proposal_url)

            return self._handle_fetch_proposal_response(response)

    def _clean_partial_votes(self, votes):
        
        for idx, vote in enumerate(votes):
            votes[idx] = re.sub(r"\d+\W+", '', vote).strip()

        return votes

    def _parse_vote_type(self):
        pass

    def _parse_voting_results(self, votes_element):
        votacoes = votes_element

        votos_contra = []
        votos_afavor = []
        votos_abstencao = []
        votos_ausencia = []
        
        if(len(votacoes) > 0):
            votacoes = votacoes[-1]
            votos = votacoes.text_content()

            CONTRA = "#contra:"
            AFAVOR = "#a_favor:"
            ABSTENCAO = "#abstencao:"
            AUSENCIA = "#ausencia:"

            votos = votos.replace("Contra:",CONTRA)
            votos = votos.replace("A Favor:",AFAVOR)
            votos = votos.replace("Abstenção:",ABSTENCAO)
            votos = votos.replace("Ausência:",AUSENCIA)
            
            if("#" not in votos):
                return

            if(CONTRA in votos):
                start_str_idx = votos.index(CONTRA) + len(CONTRA)
                end_str_idx = len(votos)
                try:
                    end_str_idx = votos.index("#",start_str_idx)
                except:
                    pass                    
                in_conta = votos[start_str_idx:end_str_idx]
                votos_contra = in_conta.strip().split(",")

            if(AFAVOR in votos):
                start_str_idx = votos.index(AFAVOR) + len(AFAVOR)
                end_str_idx = len(votos)
                try:
                    end_str_idx = votos.index("#",start_str_idx)
                except:
                    pass
                in_conta = votos[start_str_idx:end_str_idx]
                votos_afavor = in_conta.strip().split(",")

            if(ABSTENCAO in votos):
                start_str_idx = votos.index(ABSTENCAO) + len(ABSTENCAO)
                end_str_idx = len(votos)
                try:
                    end_str_idx = votos.index("#",start_str_idx)
                except:
                    pass
                in_conta = votos[start_str_idx:end_str_idx]
                votos_abstencao = in_conta.strip().split(",")  

            if(AUSENCIA in votos):
                start_str_idx = votos.index(AUSENCIA) + len(AUSENCIA)
                end_str_idx = len(votos)
                try:
                    end_str_idx = votos.index("#",start_str_idx)
                except:
                    pass
                in_conta = votos[start_str_idx:end_str_idx]
                votos_ausencia = in_conta.strip().split(",")  
              

        votos_contra = [x.strip() for x in votos_contra]
        votos_afavor = [x.strip() for x in votos_afavor]
        votos_abstencao = [x.strip() for x in votos_abstencao]
        votos_ausencia = [x.strip() for x in votos_ausencia]
        
        all_votes = {
                    "contra":self._clean_partial_votes(votos_contra),
                    "afavor":self._clean_partial_votes(votos_afavor), 
                    "abstencao":self._clean_partial_votes(votos_abstencao),
                    "ausencia":self._clean_partial_votes(votos_ausencia)
                    }
        
        return all_votes
    
    def _parse_party_from_author_name(self, s):
        return s[s.find("(")+1:s.find(")")]

    def _parse_html(self, html_content):
        tree = html.fromstring(html_content)
        
        title = tree.xpath("//span[contains(@id, 'ucLinkDocumento_lblDocumentoTitulo')]")
        if(len(title) == 0):
            logger.error("non existent")
            return

        pdfLink = tree.xpath("//a[contains(@id, 'ucLinkDocumento_hplDocumentoPDF')]")
        print("pdfLink",pdfLink)
        proposedBy = tree.xpath("//span[contains(@id, 'lblDeputadosGP')]")
        dataVotacao = tree.xpath("//span[contains(@id, 'lblData')]")
        resultadosVotacao = tree.xpath("//span[contains(@id, 'lblResultado')]")
        votosProposta = self._parse_voting_results(tree.xpath("//span[contains(@id, 'IniciativaFase_Detalhe_PLC1_ucVotacoes_rptVotacoes_ctl00_lblDetalhes')]"))
        comissao_elements = tree.xpath("//span[contains(@id, 'ucActividadeComissao_lblNome')]")
        
        authors = []
        authors_elements = tree.xpath("//a[contains(@id, 'hplAutor')]")
        for author in authors_elements:
            authors.append({"name":author.text, "bioURL":author.get("href")})

        comissoes = []
        comissoes_elements = tree.xpath("//span[contains(@id, 'ucActividadeComissao_lblNome')]")
        for comissao in comissoes_elements:
            comissoes.append(comissao.text)

        comissoes = list(set(comissoes))

        dataVotacao_s = dataVotacao[0].text
        dataVotacao_d = datetime.strptime(dataVotacao_s, '%Y-%m-%d')

        print("pdfLink",pdfLink)
        print("len(pdfLink)",len(pdfLink))

        if(len(pdfLink) == 0):
            return 

        doc = {
            "title":title[0].text,
            "pdfLink":pdfLink[0].get("href"),
            "dataVotacao":dataVotacao_d,
            "authors":authors,
            "comissoes":comissoes,
            "votos":votosProposta
        }

        doc["anoVotacao"] = dataVotacao_d.year        
        
        if(len(proposedBy) > 0):
            doc["proposedBy"] = proposedBy[0].text

        elif(len(authors) > 0):
            doc["proposedBy"] = self._parse_party_from_author_name(authors[0]["name"])
            
        else:
            doc["proposedBy"] = "Governo"
            
        if(len(resultadosVotacao) > 0):
            doc["resultadoFinal"] = resultadosVotacao[-1].text_content()
        
        return doc