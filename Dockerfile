FROM cgr.dev/chainguard/python:latest-dev as builder

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt --user

ENTRYPOINT [ "python", "/app/ovh-dns-updater.py" ]
