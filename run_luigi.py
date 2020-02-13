# -*- coding: UTF-8 -*-
import time
import random
import json
import datetime
import subprocess
import os

import pymongo
from bson import json_util
import requests
import pandas as pd

import luigi
from luigi.format import UTF8
from luigi.contrib.s3 import S3Target, S3Client

from meuparlamento.harvester import PortugueseParlamentProposalsHarvester
from meuparlamento.readability import ReadabilityScore
from meuparlamento.pdf import PDFReader 
from meuparlamento.nlp import ContentSummarizer
from meuparlamento.utils import translate_comission_category

MONGO_URI = os.environ.get("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME", "meuParlamento")
WORKING_DIR = os.environ.get("WORKING_DIR", "./")

class HarvestConfig(luigi.Config):
    proposal_url_template = luigi.Parameter()
    webarchive_url_replay = luigi.Parameter()
    rscript_pdf_parser = luigi.Parameter()
    rscript_sampling_probabilities = luigi.Parameter()

class BaseLuigiTask(luigi.Task):    
    def handleOutputDestination(self, destination, output_format=luigi.format.UTF8):
        if("s3://" in destination):            
            return [luigi.contrib.s3.S3Target(destination, format=output_format)]
        else:
            return [luigi.LocalTarget(destination, format=output_format)]

class PDFDownloader(BaseLuigiTask):    
    proposal_id = luigi.IntParameter()

    def requires(self):
        return [
            ProposalFetcher(proposal_id=self.proposal_id)
            ]

    def output(self):
        output_file = "results/pdfs/{0}.pdf".format(self.proposal_id)
        return [luigi.LocalTarget(os.path.join(WORKING_DIR, output_file), format=luigi.format.Nop)]

    def run(self,):        
        with self.input()[0][0].open() as fin:
            with self.output()[0].open('w') as fout:
                for line in fin:
                    doc = json.loads(line) 

                    if(doc):
                        r = requests.get(doc["pdfLink"])

                        if(r.status_code == 200):
                            fout.write(r.content)

class PDFTextParser(BaseLuigiTask):
    proposal_id = luigi.IntParameter()
 
    def requires(self):
        return [
            PDFDownloader( proposal_id=self.proposal_id)
            ]

    def output(self):  
        output_file = "results/pdfs_contents/{}.txt".format(self.proposal_id)
        return [luigi.LocalTarget(os.path.join(WORKING_DIR, output_file), format=UTF8)]

    def run(self):
        with self.input()[0][0].open("rb") as fin:
            with self.output()[0].open('w') as fout:
            
                content = PDFReader.pdf2text(fin)
                fout.write(content)

class PDFTextParserRScript(BaseLuigiTask):
    proposal_id = luigi.IntParameter()
 
    def requires(self):
        return [
           PDFDownloader( proposal_id=self.proposal_id)
        ]

    def output(self):        
        output_file = "results/pdfs_summary/{}.txt".format(self.proposal_id)
        return [luigi.LocalTarget(os.path.join(WORKING_DIR, output_file), format=UTF8)]

    def run(self):
        with self.input()[0][0].open("rb") as fin:
            with self.output()[0].open('w') as fout:
                
                print("self.input()[0][0].path",self.input()[0][0].path)
                content = PDFReader.pdf2summary(HarvestConfig().rscript_pdf_parser, self.input()[0][0].path)
                if(content):
                    fout.write(content)

class ProposalFetcher(BaseLuigiTask):
    proposal_id = luigi.IntParameter()

    def output(self):
        output_file = "results/raw/proposal_{}.json".format(self.proposal_id)
        return [luigi.LocalTarget(os.path.join(WORKING_DIR, output_file), format=UTF8)]

    def run(self):
        # collect, but be nice to the server
        time.sleep(random.randrange(1, 100)/100)
        proposalsHarvester = PortugueseParlamentProposalsHarvester(HarvestConfig())

        with self.output()[0].open('w') as f:

            doc_proposal = proposalsHarvester.fetch_proposal(self.proposal_id)                                          
            #persist output
            f.write("{}\n".format(json.dumps(doc_proposal, default=json_util.default)))

class SimplifyDocumentSchema(BaseLuigiTask):
    proposal_id = luigi.IntParameter()

    def requires(self):
        return [
            ProposalContentAnalysis(proposal_id=self.proposal_id)
            ]
    
    def output(self):
        output_file = "results/final_schema/proposal_{}.json".format(self.proposal_id)
        return [luigi.LocalTarget(os.path.join(WORKING_DIR, output_file), format=UTF8)]

    def run(self):
        with self.output()[0].open('w') as f:
        
            with self.input()[0][0].open() as fin:
                for line in fin:
                    
                    doc = json.loads(line) 
                    
                    # check if it was voted
                    # if("resultadoFinal" not in doc.keys()):
                    #     continue

                    categorias_comissoes = [translate_comission_category(comissao) for comissao in doc["comissoes"]]

                    simple_proposal_doc = {
                        "last_update":datetime.datetime.now(),
                        "title":doc["title"],
                        "authors":doc["authors"],
                        "BID":doc["BID"],
                        "pdfLink":doc["pdfLink"],
                        "comissoes":doc["comissoes"],
                        "categorias_comissoes":categorias_comissoes,
                        "votos":doc["votos"],
                        "anoVotacao":doc["anoVotacao"],
                        "proposedBy":doc["proposedBy"],
                        # "resultadoFinal":doc["resultadoFinal"],
                        "url":doc["url"],
                        "source_domain":doc["source_domain"],
                    } 

                    simple_proposal_doc["dataVotacao"] = doc["dataVotacao"]["$date"]
                    simple_proposal_doc["metadata"] = {
                        "is_governo":doc["metadata"]["is_governo"],
                        "is_oposition":doc["metadata"]["is_oposition"],
                        "readability_score":doc["metadata"]["readability_score"],
                        "num_chars":doc["metadata"]["num_chars"],
                        "num_tokens":doc["metadata"]["num_tokens"],
                        
                        #pdf content
                        "proposal_summary":doc["metadata"]["pdf"]["summary"],
                        "proposal_summary_num_chars":len(doc["metadata"]["pdf"]["summary"]),
                    }

                    if(simple_proposal_doc["metadata"]["proposal_summary"] is not ""):
                        #persist proposal
                        f.write("{}\n".format(json.dumps(simple_proposal_doc, default=json_util.default)))                    

class ProposalDatabasePersistence(BaseLuigiTask):
    proposal_id = luigi.IntParameter()

    def requires(self):
        ##setup mongodb connection
        self.mongo_conn=pymongo.MongoClient(MONGO_URI)
        self.mongo_conn_database = self.mongo_conn[MONGO_DB_NAME]
        
        #require json file with metadata
        return [
            SimplifyDocumentSchema(proposal_id=self.proposal_id)
            ]
    
    def output(self):
        return []

    def run(self):
        with self.input()[0][0].open() as fin:
            for line in fin:
                doc = json.loads(line)               
                doc["last_update"] = doc["last_update"]["$date"]
                self.mongo_conn_database["proposals"].update({'BID':doc["BID"]},{'$set':doc},upsert = True)

class ProposalContentAnalysis(BaseLuigiTask):
    proposal_id = luigi.IntParameter()

    def requires(self):        
        return [
            # proposal crawler
            ProposalFetcher(proposal_id=self.proposal_id),

            # download proposal pdf
            #PDFTextParser(proposal_id=self.proposal_id),
            PDFTextParserRScript(proposal_id=self.proposal_id),
        ]

    def output(self):
        output_file = "results/content/proposal_{}.json".format(self.proposal_id)
        return [luigi.LocalTarget(os.path.join(WORKING_DIR, output_file), format=UTF8)        ]

    def run(self):
        pdf_content = ""
        doc = {}

        with self.input()[1][0].open("r") as fin:
            pdf_content = fin.read()    

        with self.input()[0][0].open("r") as fin:
            for line in fin:
                doc = json.loads(line) 

        with self.output()[0].open('w') as fout:

            proposal_metadata = ReadabilityScore().compute(doc)   
            if(proposal_metadata):
                doc["metadata"] = proposal_metadata

            #pdf_content_metadata = ContentSummarizer(limit_sentences=3).compute(pdf_content)
            pdf_content_metadata = pdf_content

            if(pdf_content_metadata):    
                
                doc["metadata"]["pdf"] = {
                    "summary" : pdf_content
                }
            
                fout.write("{}\n".format(json.dumps(doc, default=json_util.default)))

class JoinProposalDataAndProbabilities(BaseLuigiTask):
    offset = luigi.IntParameter(default=0)
    limit = luigi.IntParameter(default=10)

    def requires(self):
        return [
            ComputeProbabilities(offset=self.offset, limit=self.limit)
            ]

    def output(self):
        output_file = "results/final/proposals_{offset}_{limit}.csv".format(offset= self.offset, limit =self.limit)
        output_filepath = os.path.join(WORKING_DIR, output_file)

        return self.handleOutputDestination(output_filepath, output_format=UTF8)

    def run(self):
        probs_df = pd.read_csv(self.input()[0][0].path)
        print(probs_df.head())
        requires = []
        max_range_id =  self.offset + self.limit        

        with self.output()[0].open('w') as fout:
            for proposalId in range(self.offset, max_range_id):
                #yield ProposalFetcher(proposal_id=proposalId)
                try:
                    req = SimplifyDocumentSchema(proposal_id=proposalId)
                    requires.append(req)
                except:
                    print("erro",proposalId)


            data = []
            for y in requires:
                
                # try:
                res = yield y
                fin = res[0].open('r')

                for line in fin:
                    doc = json.loads(line) 

                    probab = probs_df[probs_df['BID'] == int(doc["BID"])]["Probab"]
                    print(doc["BID"],probab.iloc[0])

                    doc["metadata"]["probability"] = probab.iloc[0]
                    fout.write("{}\n".format(json.dumps(doc, default=json_util.default)))
                # except:
                #     print("error")

class ComputeProbabilities(BaseLuigiTask):
    offset = luigi.IntParameter(default=0)
    limit = luigi.IntParameter(default=10)

    def requires(self):
        return [
            AggregateAllVotingData(offset=self.offset, limit=self.limit)
            ]

    def output(self):
        output_file = "results/probabilities/probabilities_{offset}_{limit}.csv".format(offset= self.offset, limit =self.limit)
        output_filepath = os.path.join(WORKING_DIR, output_file)

        return self.handleOutputDestination(output_filepath, output_format=UTF8)

    def run(self):
        input_file  = self.input()[0][0].path
        
        # create temp output file for R
        tmp_file = luigi.LocalTarget(is_tmp=True)
        
        cmd = "Rscript {rscript} {input_file} {output_file}".format(rscript=HarvestConfig().rscript_sampling_probabilities, 
        input_file=input_file, 
        output_file=tmp_file.path)
        
        print(cmd)
        process = subprocess.Popen([cmd],stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        process.wait()
        
        tmp_result = tmp_file.open("r").read()

        with self.output().open('w') as fout:
            fout.write(tmp_result)
            
class AggregateAllVotingData(BaseLuigiTask):
    offset = luigi.IntParameter(default=0)
    limit = luigi.IntParameter(default=10)

    def output(self):
        output_file = "results/probabilities/aggregated_voting_data_{offset}_{limit}.csv".format(offset= self.offset, limit =self.limit)
        output_filepath = os.path.join(WORKING_DIR, output_file)

        return self.handleOutputDestination(output_filepath, output_format=UTF8)
            
    def decode_vote(self, party, row):
        if party in row["votos"]["afavor"]:
            return 1
        elif party in row["votos"]["contra"]:
            return -1
        elif party in row["votos"]["abstencao"]:
            return 0
        else:
            return None
            
    def run(self):
        requires = []
        max_range_id =  self.offset + self.limit
        
        for proposalId in range(self.offset, max_range_id):
            #yield ProposalFetcher(proposal_id=proposalId)
            try:
                req = SimplifyDocumentSchema(proposal_id=proposalId)
                requires.append(req)
            except:
                print("erro",proposalId)

        with self.output()[0].open('w') as fout:
            
            data = []
            for y in requires:
                
                try:
                    res = yield y
                    fin = res[0].open('r')

                    for line in fin:
                        doc = json.loads(line) 

                        simple_vote_data = {
                            "BID":doc["BID"],
                            "proposedBy":doc["proposedBy"],
                            "is_governo":doc["metadata"]["is_governo"],

                            "readability_score":doc["metadata"]["readability_score"],
                            "num_chars":doc["metadata"]["num_chars"]
                        }
                        
                        # "metadata.is_governo":True, 
                        # "metadata.readability_score": 0, 
                        # "metadata.num_chars":{"$lte":150}
                        
                        simple_vote_data["PSD"] = self.decode_vote("PSD", doc)
                        simple_vote_data["PS"] = self.decode_vote("PS", doc)
                        simple_vote_data["CDS_PP"] = self.decode_vote("CDS_PP".replace("_","-"), doc)
                        simple_vote_data["PCP"] = self.decode_vote("PCP", doc)
                        simple_vote_data["BE"] = self.decode_vote("BE", doc)
                        simple_vote_data["PEV"] = self.decode_vote("PEV", doc)
                        simple_vote_data["PAN"] = self.decode_vote("PAN", doc)

                        data.append(simple_vote_data)
                        
                    fin.close()
                except:
                    print("ignore error")
                    pass


            data_df = pd.DataFrame(data)
            data_df.to_csv(fout)

class RefreshCacheFromLambdaFunction(luigi.Task):
    function_name = luigi.Parameter(default="meuparlamento-backend-api-test")

    # def requires(self):
    #     return [AggregateAllVotingData(offset=self.offset, limit=self.limit)]

    def run(self):
        # self.function_name = "meuparlamento-backend-api-test"
        # get_env_cmd = 'aws lambda get-function-configuration --function-name {}'.format(function_name).split()
        # response = subprocess.check_output(get_env_cmd, stderr=subprocess.STDOUT)
        # enviroment = json.loads(response)["Environment"]

        foo_desc = "Last update at {}".format(datetime.datetime.now().strftime("%Y%m%dT%H%m%s")).replace(" ","_")
        get_env_cmd = 'aws lambda update-function-configuration --function-name {} --description "{}"'.format(self.function_name, foo_desc).split()
        
        try:
            response = subprocess.check_output(get_env_cmd, stderr=subprocess.STDOUT)
            print(response)
        except subprocess.CalledProcessError as e:
            print("Failed to execute command: {}" % get_env_cmd)
            raise e

        # enviroment = json.loads(response)["Environment"]


class HarvestBatch(luigi.WrapperTask):
    offset = luigi.IntParameter(default=0)
    limit = luigi.IntParameter(default=10)

    def requires(self):
        return []

    def output(self):
        return []

    def run(self):
        max_range_id =  self.offset + self.limit
        
        for proposalId in range(self.offset,max_range_id):       
            # collect, but be nice to the server
            time.sleep(random.randrange(1, 100)/100)

            #yield ProposalFetcher(proposal_id=proposalId)
            try:
                yield SimplifyDocumentSchema(proposal_id=proposalId)
            except:
                print("erro",proposalId)

        yield ComputeProbabilities(offset=self.offset, limit=self.limit)

if __name__ == '__main__':
    luigi.run()