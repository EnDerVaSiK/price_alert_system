FROM python:3.11-slim

WORKDIR /app

# Копируем файл зависимостей конкретного сервиса
COPY practice2/services/api-gateway/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем общую директорию (модели БД)
COPY practice2/services/shared /app/shared

# Копируем код самого сервиса
COPY practice2/services/api-gateway /app/api-gateway

# Переходим в папку сервиса, чтобы корректно запустить main.py
WORKDIR /app/api-gateway

CMD ["python", "main.py"]
