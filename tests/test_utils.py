# -*- coding: UTF-8 -*-

import re

def _clean_partial_votes(votes):
    
    for idx, vote in enumerate(votes):
        votes[idx] = re.sub(r"\d+\W+", '', vote).strip()

    return votes

class TestUtils:

    def test__clean_partial_votes(self):    

        votes =   {
                "contra" : [
                    "PS",
                    "93-BE",
                    "PCP",
                    "45-PEV"
                ],
                "afavor" : [
                    "CDS-PP"
                ],
                "abstencao" : [
                    "PSD"
                ],
                "ausencia": [
                    "PAN"
                ]
            }            

        assert _clean_partial_votes(votes["contra"]) == votes["contra"]
        assert _clean_partial_votes(votes["contra"]) == ["PS","BE","PCP","PEV"]