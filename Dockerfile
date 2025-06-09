FROM mirror.gcr.io/library/python:3.11-slim AS builder

RUN pip install --upgrade pip

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

FROM gcr.io/distroless/python3-debian12:nonroot
ARG PYTHON_VERSION=3.11

ENV PYTHONUNBUFFERED 1

COPY --from=builder /usr/local/lib/python${PYTHON_VERSION}/site-packages /usr/local/lib/python${PYTHON_VERSION}/site-packages

COPY . /app
WORKDIR /app


ENV PYTHONPATH=/usr/local/lib/python${PYTHON_VERSION}/site-packages

CMD ["python", "ovh-dns-updater.py"]
ENV PYTHONPATH=/usr/local/lib/python${PYTHON_VERSION}/site-packages