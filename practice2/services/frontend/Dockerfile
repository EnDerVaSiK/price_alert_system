FROM node:20-alpine

WORKDIR /app

COPY package*.json ./

# Увеличиваем таймауты и отключаем строгий SSL (помогает при блокировках провайдеров)
RUN npm config set fetch-retry-maxtimeout 120000 && \
    npm config set fetch-retries 5 && \
    npm config set strict-ssl false

# Запускаем установку с флагом --verbose, чтобы видеть каждый шаг
RUN npm install --verbose

COPY . .

EXPOSE 5173

CMD ["npm", "run", "dev", "--", "--host"]