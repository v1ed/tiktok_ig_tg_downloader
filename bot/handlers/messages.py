from aiogram import Router, F
from aiogram.types import Message, FSInputFile
from bot.services.downloader import VideoDownloader
from bot.services.compressor import VideoCompressor
import logging

logger = logging.getLogger(__name__)
router = Router()
downloader = VideoDownloader()
compressor = VideoCompressor()

@router.message(F.text.regexp(r'(https?://[^\s]+)'))
async def handle_video_link(message: Message):
    url = message.text.strip()
    
    if not downloader.is_valid_url(url):
        logger.warning("Unsupported URL from user_id=%s", message.from_user.id if message.from_user else None)
        return

    logger.info("Video request from user_id=%s", message.from_user.id if message.from_user else None)
    status_msg = await message.answer("⏳ Загрузка...")
    
    # Распаковываем кортеж (путь и размер)
    file_path, _ = await downloader.download_video(url)
    
    if file_path:
        try:
            send_path = await compressor.compress_if_needed(file_path)

            await message.answer_video(
                video=FSInputFile(send_path),
                caption=None
            )
            await status_msg.delete()
            logger.info("Video sent to user_id=%s", message.from_user.id if message.from_user else None)
        except Exception:
            logger.exception("Video send failed for user_id=%s", message.from_user.id if message.from_user else None)
            await status_msg.edit_text("❌ Ошибка при отправке видео.")
        finally:
            downloader.remove_file(file_path)
            if 'send_path' in locals() and send_path != file_path:
                downloader.remove_file(send_path)
    else:
        logger.warning("Video download returned no file")
        await status_msg.edit_text("❌ Не удалось скачать видео. Попробуйте позже.")
