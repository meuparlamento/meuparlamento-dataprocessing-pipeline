# Base image https://hub.docker.com/u/rocker/
FROM rocker/r-base:latest

ADD . /code
WORKDIR /code

RUN Rscript install_packages.R

RUN apt-get update -y
RUN apt-get install -y git curl python3.7 python3-pip

RUN pip3 install -r requirements.txt
RUN alias python="/usr/bin/python3"

EXPOSE 8082

# CMD ["luigid", "--background","--port=8082", "--logdir=logs"]
CMD ["luigid", "--port=8082"]