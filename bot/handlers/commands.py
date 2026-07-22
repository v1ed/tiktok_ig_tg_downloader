import logging

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message

router = Router()
logger = logging.getLogger(__name__)

@router.message(CommandStart())
async def cmd_start(message: Message):
    logger.info("Start command from user_id=%s", message.from_user.id if message.from_user else None)
    await message.answer("Привет! Отправь мне ссылку на TikTok или Instagram Reels, и я пришлю тебе видео.")
