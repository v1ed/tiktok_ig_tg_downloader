import asyncio
import logging
from aiogram import Bot, Dispatcher
from bot.core.config import config
from bot.handlers import commands, messages, inline

async def main():
    logging.basicConfig(level=logging.INFO)
    
    bot = Bot(token=config.bot_token)
    dp = Dispatcher()

    dp.include_routers(
        commands.router,
        messages.router,
        inline.router
    )

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())