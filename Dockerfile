FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .

RUN mkdir outdir

RUN pip install -r requirements.txt

COPY . /app

CMD ["python", "gen_rss.py"]