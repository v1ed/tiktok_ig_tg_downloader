import asyncio
import logging
from aiogram import Bot, Dispatcher
from bot.core.config import config
from bot.handlers import commands, messages, inline

async def main():
    logging.basicConfig(
        level=getattr(logging, config.log_level, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )
    logger = logging.getLogger(__name__)
    
    bot = Bot(token=config.bot_token)
    dp = Dispatcher()

    dp.include_routers(
        commands.router,
        messages.router,
        inline.router
    )

    logger.info("Bot started")
    try:
        await dp.start_polling(bot)
    finally:
        logger.info("Bot stopped")
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
