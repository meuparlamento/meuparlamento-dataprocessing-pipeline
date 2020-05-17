from probabilities_tasks import AggregateAllVotingDataLocal, ComputeProbabilitiesLocal, JoinProposalDataAndProbabilitiesLocal

from luigi import scheduler, worker

import os
import os.path
from pathlib import Path
import shutil

def update_probabilities():
    input_path = "results/final_schema"

    results_path = Path("results/probabilities")
    if results_path.exists():
        shutil.rmtree(results_path)

    proposals_file = Path("results/final")
    if proposals_file.exists():
        shutil.rmtree(proposals_file)        

    # run pipeline
    w = worker.Worker()

    w.add(AggregateAllVotingDataLocal(input_dir=input_path))
    w.run()

    w.add(ComputeProbabilitiesLocal(input_dir=input_path))
    w.run()

    w.add(JoinProposalDataAndProbabilitiesLocal(input_dir=input_path))
    w.run()

if __name__ == "__main__":
    update_probabilities()