# meuparlamento-dataprocessing-pipeline

Pipeline for data ingestion, refinement and transformation.
This pipeline is responsible to parsing html, downloading pdfs and processing their content in order to provide data to [meuparlamento-backend-api](http://github.com/meuparlamento/meuparlamento-backend-api).


### Requirements

* [Python version >= 3.7](https://www.python.org/)
* [R version >= 3.6.1](https://www.r-project.org) 
* [Mongodb](https://www.mongodb.com/)
 
## Install dependecies

Install python dependencies using pip and virtualenv:

```sh 
pip install venv
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
```
Using conda:

```sh  
conda install --file requirements.txt
```

Install R packages:

```sh
Rscript install_packages.R
```

## Start Luigi Server

Make sure luigi scheduler is running so we can submit our tasks.

```sh 
luigid --background --port=8082 --logdir=logs
```

Check dashboard at http://localhost:8082

#### List of available tasks


| #Task name                        | #Arguments            | #Description          |
|-----------------------------------|-----------------------|-----------------------|
| PDFDownloader                     | proposal-id           | Download pdf file
| PDFTextParserRScript              | proposal-id           | Parse pdf and compute text summary
| ProposalFetcher                   | proposal-id          | Get html page and parse proposal's properties
| ProposalContentAnalysis           | proposal-id           | Compute readability score
| SimplifyDocumentSchema            | proposal-id          | Aggregates data into our document schema used in our backend-api
| ProposalDatabasePersistence       | proposal-id           | Persist document into MongoDB collection 
| JoinProposalDataAndProbabilities  | offset, limit         | Runs all previous tasks joining all voting and proposals data
| ComputeProbabilities              | offset, limit         | Compute inverse probability for each proposal
| AggregateAllVotingData            | offset, limit         | Aggregate all voting data into single file
| RefreshCacheFromLambdaFunction    | lambda function name  | Restart AWS Lambda function  
 
#### Running tasks
Example running task *ProposalContentAnalysis*

```sh 
python run_luigi.py ProposalContentAnalysis --proposal-id=40001
```

In order to run the entire pipeline starting from proposal id 38500 and processing the next 3500 proposals:

```sh 
python run_luigi.py JoinProposalDataAndProbabilities --offset 38500 --limit 3500
```

Or simply use the bash script:

```sh
./run_pipeline.sh 38500 3500
```

## Environment customization 

By default we have the following environment variables:

```sh
MONGO_URI = "mongodb://localhost:27017"
MONGO_DB_NAME = "meuParlamento"
WORKING_DIR = "./"
```

You can change these environment variables as you wish.

## Support Amazon S3 Storage
**WORKING_DIR ** supports S3 Buckets, so you can specify your own working dir as the following example : 

```sh
export WORKING_DIR = "s3://{bucketname}/meuparlamento/output"
```

## Testing
To run tests you can use [pytest](https://pytest.org):

```sh
pytest
```


## Docker

We prepared a Docker container descriptor that provides all requirements properly installed.
The first step is the build the container. This may take a while.

```sh
docker build -t meuparlamento-pipeline .
```

Once you have built the container you can run it using the following command. 

```sh
docker run --name meuparlamento-pipeline --publish=0.0.0.0:8082:8082 meuparlamento-pipeline
```

Check Luigi dashboard at http://0.0.0.0:8082

Now you can run all tasks as the following example:

```sh
docker exec -i meuparlamento-pipeline /usr/bin/python3 run_luigi.py [TASK_NAME] [ARGUMENTS]
```

Example:

```sh
docker exec -i meuparlamento-pipeline /usr/bin/python3 run_luigi.py ProposalContentAnalysis --proposal-id=38950
```

## Meta

Team meuParlamento.pt dev@meuparlamento.pt

Distributed under the GPL license. See ``LICENSE`` for more information.

[https://github.com/meuparlamento](https://github.com/meuparlamento)

## Contributing

1. Fork it (<https://github.com/meuparlamento/meuparlamento-dataprocessing-pipeline/fork>)
2. Create your feature branch (`git checkout -b feature/fooBar`)
3. Commit your changes (`git commit -am 'Add some fooBar'`)
4. Push to the branch (`git push origin feature/fooBar`)
5. Create a new Pull Request