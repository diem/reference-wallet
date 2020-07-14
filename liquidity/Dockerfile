FROM python:3.7-slim

WORKDIR /liquidity

RUN apt-get update && apt-get install -y gcc
RUN apt-get install -y curl netcat
RUN pip install pipenv

COPY liquidity/Pipfile liquidity/Pipfile.lock ./
RUN pipenv lock --requirements > requirements.txt
RUN pip install -r requirements.txt

COPY backend/libra_utils/ /backend/libra_utils
COPY wait.sh /
COPY liquidity/ .
