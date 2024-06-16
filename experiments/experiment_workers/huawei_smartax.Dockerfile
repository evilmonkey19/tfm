FROM python:3.12-slim

ARG HOSTNAME=generic_hostname
ARG PORT=9000

RUN apt-get update && apt-get install -y git 

RUN pip install netmiko ntc-templates wonderwords pyyaml jinja2

RUN pip install git+https://github.com/fakenos/fakenos.git@road_to_thesis

WORKDIR /app

COPY . /app

# CMD ["tail", "-f", "/dev/null"]