FROM python:3.11-slim

WORKDIR /app

COPY practice2/services/analyzer/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY practice2/services/shared /app/shared
COPY practice2/services/analyzer /app/analyzer

WORKDIR /app/analyzer

CMD ["python", "main.py"]
