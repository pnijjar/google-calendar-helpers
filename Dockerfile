FROM python:3.9-slim

WORKDIR /app

COPY . /app

RUN mkdir outdir

RUN pip install -r requirements.txt
