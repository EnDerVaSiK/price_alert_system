FROM python:3.11-slim

WORKDIR /app

COPY practice2/services/notifier/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY practice2/services/shared /app/shared
COPY practice2/services/notifier /app/notifier

WORKDIR /app/notifier

CMD ["python", "main.py"]
