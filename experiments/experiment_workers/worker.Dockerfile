FROM python:3.12-slim

ARG LOCATION=generic_location

RUN pip install celery

WORKDIR /app

COPY tasks.py ./tasks.py

CMD ["celery", "-A", "tasks", "worker", "-n", "${LOCATION}", "-Q", "${LOCATION},celery", "--loglevel=info"]
