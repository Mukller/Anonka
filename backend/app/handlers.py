from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from sqlalchemy.orm import Session
from datetime import datetime
from .models import User, Thread, Message as DBMessage, Response
import json

router = Router()


def get_or_create_user(db: Session, telegram_id: int, username: str = None):
    user = db.query(User).filter_by(telegram_id=telegram_id).first()
    if not user:
        user = User(telegram_id=telegram_id, username=username)
        db.add(user)
        db.commit()
    return user


def get_or_create_thread(db: Session, user_id: int, group_chat_id: int, topic_id: int = None):
    thread = db.query(Thread).filter_by(user_id=user_id, group_chat_id=group_chat_id).first()
    if not thread:
        thread = Thread(user_id=user_id, group_chat_id=group_chat_id, topic_id=topic_id)
        db.add(thread)
        db.commit()
    return thread


def extract_attachments(message: Message):
    attachments = []

    if message.photo:
        attachments.append({
            "type": "photo",
            "file_id": message.photo[-1].file_id,
            "file_unique_id": message.photo[-1].file_unique_id,
        })
    elif message.video:
        attachments.append({
            "type": "video",
            "file_id": message.video.file_id,
            "file_unique_id": message.video.file_unique_id,
        })
    elif message.document:
        attachments.append({
            "type": "document",
            "file_id": message.document.file_id,
            "file_name": message.document.file_name,
            "file_unique_id": message.document.file_unique_id,
        })
    elif message.audio:
        attachments.append({
            "type": "audio",
            "file_id": message.audio.file_id,
            "file_unique_id": message.audio.file_unique_id,
        })
    elif message.voice:
        attachments.append({
            "type": "voice",
            "file_id": message.voice.file_id,
            "file_unique_id": message.voice.file_unique_id,
        })
    elif message.animation:
        attachments.append({
            "type": "animation",
            "file_id": message.animation.file_id,
            "file_unique_id": message.animation.file_unique_id,
        })
    elif message.sticker:
        attachments.append({
            "type": "sticker",
            "file_id": message.sticker.file_id,
            "file_unique_id": message.sticker.file_unique_id,
        })
    elif message.contact:
        attachments.append({
            "type": "contact",
            "phone_number": message.contact.phone_number,
            "first_name": message.contact.first_name,
        })
    elif message.location:
        attachments.append({
            "type": "location",
            "latitude": message.location.latitude,
            "longitude": message.location.longitude,
        })
    elif message.venue:
        attachments.append({
            "type": "venue",
            "latitude": message.venue.location.latitude,
            "longitude": message.venue.location.longitude,
            "title": message.venue.title,
        })

    return attachments if attachments else None


def create_thread_message(db_message: DBMessage, sender_username: str):
    text = f"📨 <b>Новое сообщение от {sender_username}</b>\n"
    text += f"⏰ {db_message.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
    text += f"🆔 ID: {db_message.sender_telegram_id}\n\n"

    if db_message.message_text:
        text += db_message.message_text

    if db_message.attachments:
        text += f"\n\n📎 Вложения: {len(json.loads(db_message.attachments)) if isinstance(db_message.attachments, str) else len(db_message.attachments)}"

    return text


def get_message_keyboard(message_id: int):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💬 Ответить", callback_data=f"reply_{message_id}"),
            InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit_{message_id}"),
        ],
        [
            InlineKeyboardButton(text="🗑️ Удалить", callback_data=f"delete_{message_id}"),
        ]
    ])
    return keyboard


@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "👋 Добро пожаловать в Telegram Anonymous Thread Bot!\n\n"
        "📝 Просто отправьте мне сообщение, и оно будет анонимно опубликовано в группе.\n"
        "Владелец группы сможет видеть ваш username и отвечать вам.\n\n"
        "✨ Поддерживаются все типы медиа: фото, видео, документы, аудио и т.д."
    )


@router.callback_query(F.data.startswith("delete_"))
async def handle_delete(query: CallbackQuery, db: Session):
    message_id = int(query.data.split("_")[1])
    db_message = db.query(DBMessage).filter_by(id=message_id).first()

    if db_message:
        db.delete(db_message)
        db.commit()
        await query.answer("✅ Сообщение удалено")
    else:
        await query.answer("❌ Сообщение не найдено", show_alert=True)
