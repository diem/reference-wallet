FROM python:3.7-slim

WORKDIR /liquidity

RUN apt-get update && apt-get install -y gcc git
RUN apt-get install -y curl netcat
RUN pip install pipenv

COPY liquidity/ .
RUN pipenv install --deploy --system

CMD /liquidity/run.sh