FROM cgr.dev/chainguard/python:latest-dev as builder

WORKDIR /app

COPY requirements.txt .

RUN pip install -r requirements.txt --user

COPY ovh-dns-updater.py .

ENTRYPOINT [ "python", "ovh-dns-updater.py" ]
