from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

router = Router()

@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer("Привет! Отправь мне ссылку на TikTok или Instagram Reels, и я пришлю тебе видео.")