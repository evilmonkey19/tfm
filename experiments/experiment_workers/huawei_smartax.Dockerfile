FROM python:3.12-slim

ARG HOSTNAME=generic_hostname

RUN apt-get update && apt-get install -y git

RUN pip install jinja2 fastapi[standard]

RUN pip install git+https://github.com/evilmonkey19/fakenos-tfm.git@road_to_thesis

WORKDIR /app

COPY . /app

# CMD ["tail", "-f", "/dev/null"]