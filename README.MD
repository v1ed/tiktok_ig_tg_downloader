# Inline бот для отправки видео с TikTok/Instagram* Reels

## Функционал

- Inline вызов бота `@nickname <share link>`
- Поддерживает TikTok и Instagram* Reels
- Работает в обычном режиме, достаточно просто отправить ссылку на видео

## Инструкция по запуску

1. Установить Docker [ссылка](https://docs.docker.com/engine/install/)
2. Создать бота через BotFather [ссылка](https://t.me/BotFather)
3. Вставить токен в .env
4. В настройках бота включить Inline режим `/setinline`, поддержку каналов (Channel Admin Rights) и отключить приватный мод `/setprivacy`
5. Создать приватный канал (нужен для корректной работы Inline режима)
6. Через бота [@userinfobot](https://t.me/userinfobot) получить ID канала
7. Вставить полученный ID в .env
8. Скачать расширение [Get cookies.txt LOCALLY](https://chromewebstore.google.com/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc)
9. Перейти на сайт Instagram*, открыть расширение и нажать Export
10. Перенести полученный файл в папку с проектом и переименовать его в `cookies.txt`
11. Запустить бота командой `docker compose up -d`

---

_Instagram принадлежит террористической и экстремистской компании Meta_