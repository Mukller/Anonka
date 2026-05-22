from aiogram import Router, F, Bot
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.filters import Command
from sqlalchemy.orm import Session
from datetime import datetime
from .models import User, Thread, Message as DBMessage, Response
import json
import logging
import asyncio

logger = logging.getLogger(__name__)
router = Router()

user_states = {}


def get_or_create_user(db: Session, telegram_id: int, username: str = None):
    user = db.query(User).filter_by(telegram_id=telegram_id).first()
    if not user:
        user = User(telegram_id=telegram_id, username=username)
        db.add(user)
        db.commit()
    else:
        if username and user.username != username:
            user.username = username
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
        attachments.append({"type": "photo", "file_id": message.photo[-1].file_id})
    elif message.video:
        attachments.append({"type": "video", "file_id": message.video.file_id})
    elif message.document:
        attachments.append({"type": "document", "file_id": message.document.file_id})
    elif message.audio:
        attachments.append({"type": "audio", "file_id": message.audio.file_id})
    elif message.voice:
        attachments.append({"type": "voice", "file_id": message.voice.file_id})
    elif message.animation:
        attachments.append({"type": "animation", "file_id": message.animation.file_id})

    return attachments if attachments else None


def create_thread_message(db_message: DBMessage, sender_username: str):
    text = f"📨 <b>Новое сообщение от @{sender_username}</b>\n"
    text += f"⏰ {db_message.created_at.strftime('%Y-%m-%d %H:%M:%S')}\n"
    text += f"🆔 Sender ID: {db_message.sender_telegram_id}\n\n"
    if db_message.message_text:
        text += db_message.message_text
    return text


def get_message_keyboard(message_id: int):
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="💬 Ответить", callback_data=f"reply_{message_id}"),
        ]
    ])
    return keyboard


@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "<b>Здравствуйте!</b>\n\n"
        "Отправьте своё сообщение и мы ответим в ближайшее время.\n"
        "Это полностью анонимно 🎭\n\n"
        "Создано с помощью @AnonCreatorBot (http://t.me/AnonCreatorBot?start=v1llanel_bot)",
        parse_mode="HTML"
    )


@router.message()
async def handle_message(message: Message, bot: Bot, db: Session, group_chat_id: int):
    try:
        user = get_or_create_user(db, message.from_user.id, message.from_user.username)

        # Проверяем, находится ли пользователь в режиме ответа
        user_state = user_states.get(message.from_user.id)

        if user_state and user_state.get("mode") == "replying":
            # Это ответ на существующее сообщение
            message_id = user_state["message_id"]
            sender_username = user_state["sender_username"]
            db_message = db.query(DBMessage).filter_by(id=message_id).first()

            if db_message:
                thread = db_message.thread
                attachments = extract_attachments(message)

                # Создаём ответ в БД
                response = Response(
                    message_id=message_id,
                    responder_user_id=message.from_user.id,
                    response_text=message.text or message.caption,
                    attachments=json.dumps(attachments) if attachments else None,
                )
                db.add(response)
                db.commit()

                # Формируем текст ответа
                response_text = f"💬 <b>Ответ на сообщение от @{sender_username}</b>\n"
                response_text += f"⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
                if message.text:
                    response_text += message.text

                # Отправляем ответ в группу
                if message.photo:
                    await bot.send_photo(group_chat_id, message.photo[-1].file_id, caption=response_text, parse_mode="HTML", message_thread_id=thread.topic_id)
                elif message.video:
                    await bot.send_video(group_chat_id, message.video.file_id, caption=response_text, parse_mode="HTML", message_thread_id=thread.topic_id)
                elif message.document:
                    await bot.send_document(group_chat_id, message.document.file_id, caption=response_text, parse_mode="HTML", message_thread_id=thread.topic_id)
                else:
                    await bot.send_message(group_chat_id, response_text, parse_mode="HTML", message_thread_id=thread.topic_id)

                # Удаляем пользователя из режима ответа
                del user_states[message.from_user.id]

                # Отправляем подтверждение
                sent_message = await message.answer("✅ Ответ отправлен", parse_mode="HTML")

                # Delete the message after 5 seconds
                async def delete_message():
                    await asyncio.sleep(5)
                    try:
                        await sent_message.delete()
                    except Exception as e:
                        logger.warning(f"Failed to delete success message: {e}")

                asyncio.create_task(delete_message())
            else:
                await message.answer("❌ Сообщение не найдено", parse_mode="HTML")
                del user_states[message.from_user.id]
        else:
            # Обычное новое анонимное сообщение
            thread = get_or_create_thread(db, user.id, group_chat_id)
            attachments = extract_attachments(message)

            db_message = DBMessage(
                thread_id=thread.id,
                sender_telegram_id=message.from_user.id,
                sender_username=message.from_user.username or f"User{message.from_user.id}",
                message_text=message.text or message.caption,
                attachments=json.dumps(attachments) if attachments else None,
            )
            db.add(db_message)
            db.commit()

            thread_text = create_thread_message(db_message, user.username or f"User{user.telegram_id}")
            keyboard = get_message_keyboard(db_message.id)

            if message.photo:
                await bot.send_photo(group_chat_id, message.photo[-1].file_id, caption=thread_text, parse_mode="HTML", reply_markup=keyboard, message_thread_id=thread.topic_id)
            elif message.video:
                await bot.send_video(group_chat_id, message.video.file_id, caption=thread_text, parse_mode="HTML", reply_markup=keyboard, message_thread_id=thread.topic_id)
            elif message.document:
                await bot.send_document(group_chat_id, message.document.file_id, caption=thread_text, parse_mode="HTML", reply_markup=keyboard, message_thread_id=thread.topic_id)
            else:
                await bot.send_message(group_chat_id, thread_text, parse_mode="HTML", reply_markup=keyboard, message_thread_id=thread.topic_id)

            sent_message = await message.answer("✅ Сообщение успешно отправлено", parse_mode="HTML")

            # Delete the message after 5 seconds
            async def delete_message():
                await asyncio.sleep(5)
                try:
                    await sent_message.delete()
                except Exception as e:
                    logger.warning(f"Failed to delete success message: {e}")

            asyncio.create_task(delete_message())
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        await message.answer(f"❌ Ошибка: {str(e)}", parse_mode="HTML")


@router.callback_query(F.data.startswith("reply_"))
async def handle_reply(query: CallbackQuery, db: Session):
    message_id = int(query.data.split("_")[1])
    user_id = query.from_user.id

    # Проверяем, что сообщение существует
    db_message = db.query(DBMessage).filter_by(id=message_id).first()

    if db_message:
        # Сохраняем, что пользователь хочет ответить на это сообщение
        user_states[user_id] = {
            "mode": "replying",
            "message_id": message_id,
            "sender_username": db_message.sender_username
        }

        await query.answer("Отправьте ваш ответ в личные сообщения боту")
    else:
        await query.answer("❌ Сообщение не найдено", show_alert=True)


@router.callback_query(F.data.startswith("delete_"))
async def handle_delete(query: CallbackQuery, db: Session):
    message_id = int(query.data.split("_")[1])
    db_message = db.query(DBMessage).filter_by(id=message_id).first()
    if db_message:
        db.delete(db_message)
        db.commit()
        await query.answer("✅ Сообщение удалено")
        await query.message.delete()
    else:
        await query.answer("❌ Не найдено", show_alert=True)
