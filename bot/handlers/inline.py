import uuid
import logging
import asyncio
from aiogram import Router, Bot
from aiogram.types import InlineQuery, InlineQueryResultVideo, FSInputFile, InlineQueryResultCachedVideo
from bot.services.downloader import VideoDownloader
from bot.services.compressor import VideoCompressor
from bot.core.config import config

logger = logging.getLogger(__name__)
router = Router()
downloader = VideoDownloader()
compressor = VideoCompressor()

@router.inline_query()
async def handle_inline(inline_query: InlineQuery, bot: Bot) -> None:
    query = inline_query.query.strip()
    if not downloader.is_valid_url(query):
        logger.debug("Ignored unsupported inline query")
        return

    logger.info("Inline video request from user_id=%s", inline_query.from_user.id)
    # 1. Загрузка файла
    file_path, _ = await asyncio.wait_for(downloader.download_video(query), timeout=25.0)
    if not file_path:
        logger.warning("Inline video download returned no file")
        return

    try:
        send_path = await compressor.compress_if_needed(file_path)
        # 2. Отправка в ПУБЛИЧНЫЙ канал
        # Убедись, что CHANNEL_ID в .env — это либо @username, либо ID публичного канала
        sent_msg = await bot.send_video(
            chat_id=config.channel_id,
            video=FSInputFile(send_path),
            caption=f"🔗 Source: {query}"
        )
        
        file_id = sent_msg.video.file_id
        logger.debug("Video cached: file_id=%s", sent_msg.video.file_id)
        
        # 3. Формируем публичную ссылку на сообщение
        # Если канал @my_channel, ссылка: https://t.me/my_channel/123
        # Если используем ID: https://t.me/c/123456789/123
        channel_link = f"https://t.me/{str(config.channel_id).replace('@', '')}/{sent_msg.message_id}"

        # 4. Формируем результат
        logger.debug("Cached video link: %s", channel_link)
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
        
        logger.info("Inline video ready for user_id=%s", inline_query.from_user.id)
    except Exception:
        logger.exception("Inline video processing failed for user_id=%s", inline_query.from_user.id)
    finally:
        downloader.remove_file(file_path)
        if 'send_path' in locals() and send_path != file_path:
            downloader.remove_file(send_path)
