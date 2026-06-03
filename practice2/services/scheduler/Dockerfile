FROM python:3.11-slim

WORKDIR /app

COPY practice2/services/scheduler/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY practice2/services/shared /app/shared
COPY practice2/services/scheduler /app/scheduler

WORKDIR /app/scheduler

CMD ["python", "main.py"]
