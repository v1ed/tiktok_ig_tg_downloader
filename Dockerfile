FROM python:3.10-alpine

# Установка ffmpeg обязательна для TikTok/Instagram
RUN apk add --no-cache ffmpeg

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot ./bot
COPY cookies.txt .

CMD ["python", "-m", "bot.main"]
