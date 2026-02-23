from aiogram import Router, F
from aiogram.types import Message, FSInputFile
from bot.services.downloader import VideoDownloader

router = Router()
downloader = VideoDownloader()

@router.message(F.text.regexp(r'(https?://[^\s]+)'))
async def handle_video_link(message: Message):
    url = message.text.strip()
    
    if not downloader.is_valid_url(url):
        return

    status_msg = await message.answer("⏳ Загрузка...")
    file_path = await downloader.download_video(url)
    
    if file_path:
        try:
            await message.answer_video(
                video=FSInputFile(file_path),
                caption=None
            )
            await status_msg.delete()
        finally:
            downloader.remove_file(file_path)
    else:
        await status_msg.edit_text("❌ Ошибка загрузки.")