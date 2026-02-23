from aiogram import Router, F
from aiogram.types import Message, FSInputFile
from bot.services.downloader import VideoDownloader
import logging

router = Router()
downloader = VideoDownloader()

@router.message(F.text.regexp(r'(https?://[^\s]+)'))
async def handle_video_link(message: Message):
    url = message.text.strip()
    
    if not downloader.is_valid_url(url):
        return

    status_msg = await message.answer("⏳ Загрузка...")
    
    # Распаковываем кортеж (путь и размер)
    file_path, file_size = await downloader.download_video(url)
    
    if file_path:
        try:
            # Проверяем лимит 50МБ для обычных сообщений тоже
            if file_size > 50:
                await status_msg.edit_text("❌ Файл слишком большой (> 50 MB)")
                downloader.remove_file(file_path)
                return

            await message.answer_video(
                video=FSInputFile(file_path),
                caption=None
            )
            await status_msg.delete()
        except Exception as e:
            logging.error(f"Send error: {e}")
            await status_msg.edit_text("❌ Ошибка при отправке видео.")
        finally:
            downloader.remove_file(file_path)
    else:
        await status_msg.edit_text("❌ Не удалось скачать видео. Попробуйте позже.")