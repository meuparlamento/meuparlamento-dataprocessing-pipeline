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


class JoinProposalDataAndProbabilitiesLocal(BaseLuigiTask):
    input_dir = luigi.Parameter(default="results/final_schema")

    def complete(self):
        """Flag this task as incomplete if any requirement is incomplete or has been updated more recently than this task"""
        import os
        import time

        def mtime(path):
            return time.ctime(os.path.getmtime(path))

        # assuming 1 output
        if not os.path.exists(self.output()[0].path):
            return False

        self_mtime = mtime(self.output().path) 

        # the below assumes a list of requirements, each with a list of outputs. YMMV
        for el in self.requires():
            if not el.complete():
                return False
            for output in el.output():
                if mtime(output.path) > self_mtime:
                    return False

        return True
        
    def requires(self):
        return [
            ComputeProbabilitiesLocal(input_dir=self.input_dir)
            ]

    def output(self):
        output_file = "results/final/proposals.csv".format()
        output_filepath = os.path.join(WORKING_DIR, output_file)

        return self.handleOutputDestination(output_filepath, output_format=UTF8)

    def run(self):
        probs_df = pd.read_csv(self.input()[0][0].path)
        print(probs_df.head())
        requires = []

        
        max_range_id = probs_df["BID"].max()
        # max_range_id =  self.offset + self.limit        

        with self.output()[0].open('w') as fout:
            input_files = os.listdir(self.input_dir)

            data = []
            for y in input_files:
                
                # try:
                if(True):
                    filename = self.input_dir + "/" + y
                    print(filename)
                    # res = open(filename, "r")
                    # fin = res[0].open('r')
                    fin = open(filename, "r")

                    for line in fin:
                        doc = json.loads(line) 
            # for proposalId in probs_df["BID"].tolist():
            #     input_files = os.listdir(self.input_dir)
                #yield ProposalFetcher(proposal_id=proposalId)
                # try:
                #     req = SimplifyDocumentSchema(proposal_id=proposalId)
                #     requires.append(req)
                # except:
                #     print("erro",proposalId)


            # data = []
            # for y in requires:
                
            #     # try:
            #     # res = yield y
            #     fin = res[0].open('r')

            #     for line in fin:
                        # doc = json.loads(line) 

                        probab = probs_df[probs_df['BID'] == int(doc["BID"])]["Probab"]
                        print(doc["BID"],probab.iloc[0])

                        doc["metadata"]["probability"] = probab.iloc[0]
                        fout.write("{}\n".format(json.dumps(doc, default=json_util.default)))
                # except:
                #     print("error")

class ComputeProbabilitiesLocal(BaseLuigiTask):
    input_dir = luigi.Parameter(default="results/final_schema")
    
    def complete(self):
        """Flag this task as incomplete if any requirement is incomplete or has been updated more recently than this task"""
        import os
        import time

        def mtime(path):
            return time.ctime(os.path.getmtime(path))

        # assuming 1 output
        if not os.path.exists(self.output()[0].path):
            return False

        self_mtime = mtime(self.output()[0].path) 

        # the below assumes a list of requirements, each with a list of outputs. YMMV
        for el in self.requires():
            if not el.complete():
                return False
            for output in el.output():
                if mtime(output.path) > self_mtime:
                    return False

        return True

    def requires(self):
        return [
            AggregateAllVotingDataLocal(input_dir=self.input_dir)
            ]

    def output(self):
        output_file = "results/probabilities/probabilities.csv".format()
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

        with self.output()[0].open('w') as fout:
            fout.write(tmp_result)

import os     
class AggregateAllVotingDataLocal(BaseLuigiTask):
    input_dir = luigi.Parameter(default="results/final_schema")

    def complete(self):
        """Flag this task as incomplete if any requirement is incomplete or has been updated more recently than this task"""
        import os
        import time

        def mtime(path):
            return time.ctime(os.path.getmtime(path))

        # assuming 1 output
        if not os.path.exists(self.output()[0].path):
            return False

        self_mtime = mtime(self.output()[0].path) 

        # the below assumes a list of requirements, each with a list of outputs. YMMV
        for el in self.requires():
            if not el.complete():
                return False
            for output in el.output():
                if mtime(output.path) > self_mtime:
                    return False

        return True
        
    def output(self):
        output_file = "results/probabilities/aggregated_voting_data.csv"
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
        input_files = os.listdir(self.input_dir)
        
        with self.output()[0].open('w') as fout:
            
            data = []
            for y in input_files:
                
                # try:
                if(True):
                    filename = self.input_dir + "/" + y
                    print(filename)
                    # res = open(filename, "r")
                    # fin = res[0].open('r')
                    fin = open(filename, "r")

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
                # except Exception as e:
                #     print("ignore error",e)
                #     pass


            data_df = pd.DataFrame(data)
            data_df.to_csv(fout)

if __name__ == '__main__':
    luigi.run()