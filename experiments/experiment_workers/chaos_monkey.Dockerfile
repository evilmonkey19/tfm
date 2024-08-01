# Use the official Python base image
FROM python:3.11.9-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the chaos_monkey-py code into the container
COPY ./chaos_monkey.py /app
