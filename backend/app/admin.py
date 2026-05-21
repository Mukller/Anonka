from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from sqlalchemy.orm import Session
from .models import User, Thread, Message as DBMessage
from .config import GROUP_CHAT_ID

router = Router()

ADMIN_ID = None  # Set via environment variable


def set_admin_id(admin_id: int):
    global ADMIN_ID
    ADMIN_ID = admin_id


def is_admin(user_id: int) -> bool:
    return ADMIN_ID is not None and user_id == ADMIN_ID


@router.message(Command("stats"))
async def cmd_stats(message: Message, db: Session):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Команда доступна только администратору")
        return
    
    total_users = db.query(User).count()
    total_threads = db.query(Thread).count()
    total_messages = db.query(DBMessage).count()
    
    stats_text = (
        "📊 <b>Статистика Anonka</b>\n\n"
        f"👥 Всего пользователей: {total_users}\n"
        f"💬 Всего тем: {total_threads}\n"
        f"📨 Всего сообщений: {total_messages}\n"
    )
    
    await message.answer(stats_text, parse_mode="HTML")


@router.message(Command("help"))
async def cmd_help(message: Message):
    help_text = (
        "📖 <b>Справка по командам</b>\n\n"
        "/start - Начало работы\n"
        "/stats - Статистика (админ)\n"
        "/help - Эта справка\n"
    )
    
    await message.answer(help_text, parse_mode="HTML")


@router.message(Command("cleanup"))
async def cmd_cleanup(message: Message, db: Session):
    if not is_admin(message.from_user.id):
        await message.answer("❌ Команда доступна только администратору")
        return
    
    # Delete messages older than 90 days
    from datetime import datetime, timedelta
    cutoff_date = datetime.utcnow() - timedelta(days=90)
    deleted = db.query(DBMessage).filter(DBMessage.created_at < cutoff_date).delete()
    db.commit()
    
    await message.answer(f"🧹 Удалено сообщений старше 90 дней: {deleted}", parse_mode="HTML")
