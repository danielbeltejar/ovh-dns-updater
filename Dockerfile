FROM python:3.11-alpine
ENV PYTHONUNBUFFERED 1

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "ovh-dns-updater.py"]
