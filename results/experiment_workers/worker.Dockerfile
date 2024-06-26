FROM python:3.12-slim

RUN apt update && apt install -y openssh-client

RUN pip install celery netmiko ntc-templates

WORKDIR /app

COPY tasks.py ./tasks.py

# CMD ["celery", "-A", "tasks", "worker", "-n", "${LOCATION}", "-Q", "${LOCATION},celery", "--loglevel=info"]
