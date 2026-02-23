import uuid
import logging
import asyncio
from aiogram import Router, Bot
from aiogram.types import InlineQuery, InlineQueryResultVideo, FSInputFile, InlineQueryResultCachedVideo
from bot.services.downloader import VideoDownloader
from bot.core.config import config

router = Router()
downloader = VideoDownloader()

@router.inline_query()
async def handle_inline(inline_query: InlineQuery, bot: Bot) -> None:
    query = inline_query.query.strip()
    if not downloader.is_valid_url(query):
        return

    # 1. Загрузка файла
    file_path, file_size = await asyncio.wait_for(downloader.download_video(query), timeout=25.0)
    if not file_path:
        return

    if file_size > 50:
        downloader.remove_file(file_path)
        return

    try:
        # 2. Отправка в ПУБЛИЧНЫЙ канал
        # Убедись, что CHANNEL_ID в .env — это либо @username, либо ID публичного канала
        sent_msg = await bot.send_video(
            chat_id=config.channel_id,
            video=FSInputFile(file_path),
            caption=f"🔗 Source: {query}"
        )
        
        file_id = sent_msg.video.file_id
        logging.info(sent_msg.video)
        
        # 3. Формируем публичную ссылку на сообщение
        # Если канал @my_channel, ссылка: https://t.me/my_channel/123
        # Если используем ID: https://t.me/c/123456789/123
        channel_link = f"https://t.me/{str(config.channel_id).replace('@', '')}/{sent_msg.message_id}"

        # 4. Формируем результат
        logging.info(channel_link)
        result = InlineQueryResultCachedVideo(
            id=sent_msg.video.file_unique_id,
            video_file_id=sent_msg.video.file_id,
            # video_url=channel_link,    # Теперь это реальная рабочая ссылка
            # mime_type="video/mp4",
            # thumbnail_url="https://raw.githubusercontent.com/aiogram/aiogram/refs/heads/dev-3.x/docs/_static/logo.png",
            title="✅ Видео готово к отправке",
            caption=""
        )

        await inline_query.answer(
            [result], 
            cache_time=300, # Кэшируем на 5 минут
            is_personal=False
        )
        
    except Exception as e:
        logging.error(f"Inline process error: {e}")
    finally:
        downloader.remove_file(file_path)