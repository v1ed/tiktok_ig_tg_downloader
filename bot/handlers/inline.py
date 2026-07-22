import asyncio
import hashlib
import logging

from aiogram import Bot, F, Router
from aiogram.types import (
    CallbackQuery,
    ChosenInlineResult,
    FSInputFile,
    InlineQuery,
    InlineQueryResultArticle,
    InlineQueryResultCachedVideo,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaVideo,
    InputTextMessageContent,
)

from bot.core.config import config
from bot.services.compressor import VideoCompressor
from bot.services.downloader import VideoDownloader

logger = logging.getLogger(__name__)
router = Router()
downloader = VideoDownloader()
compressor = VideoCompressor()

# ponytail: кэш живёт до перезапуска; добавить БД, если повторная обработка после рестарта станет проблемой.
video_cache: dict[str, tuple[str, str]] = {}
processing: dict[str, asyncio.Task] = {}
inline_messages: dict[str, set[str]] = {}
job_queries: dict[str, str] = {}


async def replace_with_video(bot: Bot, inline_message_id: str, file_id: str) -> None:
    try:
        await bot.edit_message_media(
            inline_message_id=inline_message_id,
            media=InputMediaVideo(media=file_id),
        )
        logger.info("Inline placeholder replaced with video")
    except Exception:
        logger.exception("Inline placeholder replacement failed")


async def prepare_video(query: str, bot: Bot, user_id: int) -> None:
    file_path = send_path = None
    try:
        file_path, _ = await asyncio.wait_for(downloader.download_video(query), timeout=25.0)
        if not file_path:
            logger.warning("Inline video download returned no file")
            return

        send_path = await compressor.compress_if_needed(file_path)
        sent_msg = await bot.send_video(
            chat_id=config.channel_id,
            video=FSInputFile(send_path),
            caption=f"🔗 Source: {query}",
        )
        video_cache[query] = (sent_msg.video.file_id, sent_msg.video.file_unique_id)
        for inline_message_id in inline_messages.pop(query, set()):
            await replace_with_video(bot, inline_message_id, sent_msg.video.file_id)
        logger.info("Inline video prepared for user_id=%s", user_id)
    except Exception:
        logger.exception("Inline video preparation failed for user_id=%s", user_id)
    finally:
        processing.pop(query, None)
        if file_path:
            downloader.remove_file(file_path)
        if send_path and send_path != file_path:
            downloader.remove_file(send_path)


@router.inline_query()
async def handle_inline(inline_query: InlineQuery, bot: Bot) -> None:
    query = inline_query.query.strip()
    if not downloader.is_valid_url(query):
        logger.debug("Ignored unsupported inline query")
        await inline_query.answer([], cache_time=1, is_personal=True)
        return

    logger.info("Inline video request from user_id=%s", inline_query.from_user.id)
    cached = video_cache.get(query)
    if cached:
        file_id, unique_id = cached
        await inline_query.answer(
            [InlineQueryResultCachedVideo(
                id=unique_id,
                video_file_id=file_id,
                title="✅ Видео готово к отправке",
                caption="",
            )],
            cache_time=300,
            is_personal=False,
        )
        logger.info("Cached inline video returned to user_id=%s", inline_query.from_user.id)
        return

    if query not in processing:
        processing[query] = asyncio.create_task(prepare_video(query, bot, inline_query.from_user.id))

    job_id = hashlib.sha256(query.encode()).hexdigest()[:16]
    job_queries[job_id] = query
    await inline_query.answer(
        [InlineQueryResultArticle(
            id=job_id,
            title="⏳ Видео обрабатывается",
            description="Повторите запрос через несколько секунд",
            input_message_content=InputTextMessageContent(
                message_text="⏳ Видео обрабатывается…"
            ),
            reply_markup=InlineKeyboardMarkup(inline_keyboard=[[
                InlineKeyboardButton(
                    text="🔄 Проверить готовность",
                    callback_data=f"inline_processing:{job_id}",
                )
            ]]),
        )],
        cache_time=1,
        is_personal=True,
    )


@router.chosen_inline_result()
async def handle_chosen_inline_result(result: ChosenInlineResult, bot: Bot) -> None:
    query = result.query.strip()
    logger.debug("Chosen inline result received: has_message_id=%s", bool(result.inline_message_id))
    if not result.inline_message_id:
        logger.warning("Chosen inline result has no inline_message_id")
        return

    cached = video_cache.get(query)
    if cached:
        await replace_with_video(bot, result.inline_message_id, cached[0])
    else:
        inline_messages.setdefault(query, set()).add(result.inline_message_id)
        logger.debug("Inline placeholder registered for replacement")


@router.callback_query(F.data.startswith("inline_processing:"))
async def handle_processing_callback(callback: CallbackQuery, bot: Bot) -> None:
    job_id = callback.data.rsplit(":", 1)[-1]
    query = job_queries.get(job_id)
    if not query or not callback.inline_message_id:
        logger.warning("Inline callback cannot identify the message or job")
        await callback.answer("Задание не найдено", show_alert=True)
        return

    cached = video_cache.get(query)
    if cached:
        await replace_with_video(bot, callback.inline_message_id, cached[0])
        await callback.answer("Видео готово")
    else:
        inline_messages.setdefault(query, set()).add(callback.inline_message_id)
        logger.debug("Inline placeholder registered from callback")
        await callback.answer("Видео ещё обрабатывается")
