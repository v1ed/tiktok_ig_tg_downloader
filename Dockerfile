FROM python:3.10-slim

# Установка ffmpeg обязательна для TikTok/Instagram
RUN apt-get update && apt-get install -y ffmpeg && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
# Явно копируем куки, если их нет в основном копировании
COPY cookies.txt /app/cookies.txt

CMD ["python", "-m", "bot.main"]