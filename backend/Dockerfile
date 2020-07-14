FROM python:3.7-slim

WORKDIR /libra-wallet

RUN apt-get update && apt-get install -y gcc git
RUN apt-get install -y curl netcat
RUN pip install pipenv

COPY thirdparty/ /thirdparty/
COPY wait.sh /
COPY backend/ .

RUN pipenv lock --requirements > requirements.txt

RUN pip install -r requirements.txt

