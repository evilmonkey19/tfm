FROM python:3.12-slim

RUN apt update && apt install -y openssh-client git

RUN pip install celery netmiko 

RUN pip install --upgrade --force-reinstall git+https://github.com/networktocode/ntc-templates.git@master

WORKDIR /app

COPY worker.py ./worker.py
COPY master.py ./master.py

# CMD ["celery", "-A", "tasks", "worker", "-n", "${LOCATION}", "-Q", "${LOCATION},celery", "--loglevel=info"]