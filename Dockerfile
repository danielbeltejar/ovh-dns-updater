FROM cgr.dev/chainguard/python:latest-dev as builder

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt --user

COPY ovh-dns-updater.py .

ENV PYTHONUNBUFFERED 1

ENTRYPOINT [ "python", "ovh-dns-updater.py" ]
