import asyncio
import logging
from aiogram import Bot, Dispatcher, F
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Update
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from .models import Base
from .handlers import router
from .config import BOT_TOKEN, GROUP_CHAT_ID, GROUP_TOPIC_ID, DATABASE_URL

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
Base.metadata.create_all(bind=engine)
SessionLocal = sessionmaker(bind=engine)


class DatabaseMiddleware:
    def __init__(self, db_factory):
        self.db_factory = db_factory

    async def __call__(self, handler, event, data):
        db = self.db_factory()
        data["db"] = db
        data["bot"] = data.get("bot")
        data["group_chat_id"] = GROUP_CHAT_ID
        data["group_topic_id"] = GROUP_TOPIC_ID
        try:
            return await handler(event, data)
        finally:
            db.close()


async def main():
    bot = Bot(token=BOT_TOKEN)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    dp.message.middleware(DatabaseMiddleware(SessionLocal))
    dp.callback_query.middleware(DatabaseMiddleware(SessionLocal))

    dp.include_router(router)

    logger.info("Bot started successfully")
    logger.info(f"Group Chat ID: {GROUP_CHAT_ID}")
    logger.info(f"Group Topic ID: {GROUP_TOPIC_ID}")

    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as e:
        logger.error(f"Error: {e}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
