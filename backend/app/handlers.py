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


async def ensure_forum_topic(bot: Bot, db: Session, thread, group_chat_id: int, topic_name: str, max_attempts: int = 3):
    """
    Проверяет существование форум-темы и создаёт новую, если необходимо.
    Возвращает topic_id если успешно, None если не удалось создать.
    """
    # Если topic_id уже есть, валидируем его лёгкой проверкой
    if thread.topic_id:
        try:
            # Пробуем закрыть и снова открыть тему как проверку (no-op если уже открыта)
            # Это лёгкая операция, которая проверит существование темы
            logger.info(f"Validating existing topic {thread.topic_id}")
            # Используем reopen_forum_topic — безопасная no-op если тема существует и открыта
            await bot.reopen_forum_topic(group_chat_id, thread.topic_id)
            logger.info(f"✅ Topic {thread.topic_id} validated successfully")
            return thread.topic_id
        except Exception as validate_error:
            error_str = str(validate_error).lower()
            if "message thread not found" in error_str or "topic_closed" in error_str or "not found" in error_str:
                logger.warning(f"⚠️ Topic {thread.topic_id} is invalid: {validate_error}. Will recreate.")
                thread.topic_id = None
                db.commit()
            else:
                # Другая ошибка — топик возможно существует, но что-то другое не так
                logger.warning(f"⚠️ Topic validation returned unexpected error: {validate_error}. Assuming topic exists.")
                return thread.topic_id

    # Создаём новую тему с повторными попытками
    for attempt in range(1, max_attempts + 1):
        try:
            logger.info(f"Creating forum topic '{topic_name}' (attempt {attempt}/{max_attempts}) in group {group_chat_id}")
            topic = await bot.create_forum_topic(group_chat_id, topic_name)

            # Проверяем, что вернулся валидный message_thread_id
            if not topic or not topic.message_thread_id:
                logger.error(f"❌ create_forum_topic returned invalid result: {topic}")
                if attempt < max_attempts:
                    await asyncio.sleep(2.0 * attempt)
                    continue
                return None

            thread.topic_id = topic.message_thread_id
            db.commit()
            logger.info(f"✅ Created forum topic {thread.topic_id} (attempt {attempt})")
            # Даём время Telegram на регистрацию темы
            await asyncio.sleep(1.5)
            return thread.topic_id
        except Exception as create_error:
            logger.error(f"❌ Failed to create forum topic (attempt {attempt}/{max_attempts}): {type(create_error).__name__}: {create_error}")
            if attempt < max_attempts:
                await asyncio.sleep(2.0 * attempt)
            else:
                logger.error(f"❌ All {max_attempts} attempts to create forum topic failed")
                thread.topic_id = None
                db.commit()
                return None

    return None


@router.message(Command("start"))
async def cmd_start(message: Message):
    await message.answer(
        "Здравствуйте!\n\n"
        "Отправьте своё сообщение и мы ответим в ближайшее время.\n"
        "Это полностью анонимно 🎭\n\n"
        "Создано с помощью @AnonCreatorBot"
    )


@router.message()
async def handle_message(message: Message, bot: Bot, db: Session, group_chat_id: int):
    try:
        # Игнорируем сообщения от самого бота
        if message.from_user.is_bot:
            return

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

                # Проверяем и создаём тему через helper-функцию перед отправкой ответа
                topic_name = db_message.sender_username or f"User{db_message.sender_telegram_id}"
                await ensure_forum_topic(bot, db, thread, group_chat_id, topic_name)

                # Отправляем ответ в группу
                reply_kwargs = {"parse_mode": "HTML"}
                if thread.topic_id:
                    reply_kwargs["message_thread_id"] = thread.topic_id
                    logger.info(f"Sending reply to existing topic {thread.topic_id}")
                else:
                    logger.warning(f"Reply will be sent to group without topic ID (thread {thread.id} has no topic_id)")

                try:
                    if message.photo:
                        await bot.send_photo(group_chat_id, message.photo[-1].file_id, caption=response_text, **reply_kwargs)
                    elif message.video:
                        await bot.send_video(group_chat_id, message.video.file_id, caption=response_text, **reply_kwargs)
                    elif message.document:
                        await bot.send_document(group_chat_id, message.document.file_id, caption=response_text, **reply_kwargs)
                    else:
                        await bot.send_message(group_chat_id, response_text, **reply_kwargs)
                    logger.info(f"✅ Reply sent successfully")
                except Exception as send_error:
                    logger.error(f"❌ Failed to send reply: {type(send_error).__name__}: {send_error}")
                    logger.error(f"Reply kwargs: {reply_kwargs}, original message thread_id: {thread.topic_id}")

                    # Если сообщение о том, что тема не найдена, пересоздаём тему через helper и пытаемся снова
                    if "message thread not found" in str(send_error).lower():
                        logger.warning(f"Forum topic {thread.topic_id} not found. Recreating via helper...")
                        thread.topic_id = None
                        db.commit()

                        topic_name = db_message.sender_username or f"User{db_message.sender_telegram_id}"
                        new_topic_id = await ensure_forum_topic(bot, db, thread, group_chat_id, topic_name)

                        if not new_topic_id:
                            logger.error(f"❌ Could not create new forum topic for reply")
                            raise

                        # Обновляем reply_kwargs с новым topic_id
                        reply_kwargs["message_thread_id"] = new_topic_id

                        # Пытаемся отправить ответ снова
                        logger.info(f"Retrying to send reply to new topic {new_topic_id}")
                        try:
                            if message.photo:
                                await bot.send_photo(group_chat_id, message.photo[-1].file_id, caption=response_text, **reply_kwargs)
                            elif message.video:
                                await bot.send_video(group_chat_id, message.video.file_id, caption=response_text, **reply_kwargs)
                            elif message.document:
                                await bot.send_document(group_chat_id, message.document.file_id, caption=response_text, **reply_kwargs)
                            else:
                                await bot.send_message(group_chat_id, response_text, **reply_kwargs)
                            logger.info(f"✅ Reply sent successfully to recreated forum topic")
                        except Exception as retry_error:
                            logger.error(f"❌ Failed to send reply retry: {type(retry_error).__name__}: {retry_error}")
                            raise
                    else:
                        raise

                # Отправляем ответ исходному пользователю в личное сообщение
                try:
                    user_response_text = f"💬 <b>Ответ на ваше сообщение</b>\n\n"
                    if message.text:
                        user_response_text += message.text

                    if message.photo:
                        await bot.send_photo(db_message.sender_telegram_id, message.photo[-1].file_id, caption=user_response_text, parse_mode="HTML")
                    elif message.video:
                        await bot.send_video(db_message.sender_telegram_id, message.video.file_id, caption=user_response_text, parse_mode="HTML")
                    elif message.document:
                        await bot.send_document(db_message.sender_telegram_id, message.document.file_id, caption=user_response_text, parse_mode="HTML")
                    else:
                        await bot.send_message(db_message.sender_telegram_id, user_response_text, parse_mode="HTML")
                    logger.info(f"✅ Reply sent to original user {db_message.sender_telegram_id}")
                except Exception as user_send_error:
                    logger.error(f"❌ Failed to send reply to user {db_message.sender_telegram_id}: {type(user_send_error).__name__}: {user_send_error}")

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
            logger.info(f"Got/created thread {thread.id} for user {user.id}, topic_id={thread.topic_id}")

            # Проверяем и создаём тему через helper-функцию
            topic_name = message.from_user.username or f"User{message.from_user.id}"
            await ensure_forum_topic(bot, db, thread, group_chat_id, topic_name)

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

            # Отправляем в топик если он существует
            send_kwargs = {
                "parse_mode": "HTML",
                "reply_markup": keyboard
            }
            if thread.topic_id:
                send_kwargs["message_thread_id"] = thread.topic_id

            try:
                logger.info(f"Sending message to group {group_chat_id}, kwargs: {send_kwargs}")
                if message.photo:
                    await bot.send_photo(group_chat_id, message.photo[-1].file_id, caption=thread_text, **send_kwargs)
                elif message.video:
                    await bot.send_video(group_chat_id, message.video.file_id, caption=thread_text, **send_kwargs)
                elif message.document:
                    await bot.send_document(group_chat_id, message.document.file_id, caption=thread_text, **send_kwargs)
                else:
                    await bot.send_message(group_chat_id, thread_text, **send_kwargs)
                logger.info(f"✅ Message sent successfully to group")
            except Exception as send_error:
                logger.error(f"❌ Failed to send message to group: {type(send_error).__name__}: {send_error}")
                logger.error(f"Message kwargs: {send_kwargs}, thread_id: {thread.topic_id}")

                # Если сообщение о том, что тема не найдена, пересоздаём тему через helper и пытаемся снова
                if "message thread not found" in str(send_error).lower():
                    logger.warning(f"Forum topic {thread.topic_id} not found. Recreating via helper...")
                    thread.topic_id = None
                    db.commit()

                    topic_name = message.from_user.username or f"User{message.from_user.id}"
                    new_topic_id = await ensure_forum_topic(bot, db, thread, group_chat_id, topic_name)

                    if not new_topic_id:
                        logger.error(f"❌ Could not create new forum topic after retry")
                        raise

                    # Обновляем send_kwargs с новым topic_id
                    send_kwargs["message_thread_id"] = new_topic_id

                    # Пытаемся отправить сообщение снова
                    logger.info(f"Retrying to send message to new topic {new_topic_id}")
                    try:
                        if message.photo:
                            await bot.send_photo(group_chat_id, message.photo[-1].file_id, caption=thread_text, **send_kwargs)
                        elif message.video:
                            await bot.send_video(group_chat_id, message.video.file_id, caption=thread_text, **send_kwargs)
                        elif message.document:
                            await bot.send_document(group_chat_id, message.document.file_id, caption=thread_text, **send_kwargs)
                        else:
                            await bot.send_message(group_chat_id, thread_text, **send_kwargs)
                        logger.info(f"✅ Message sent successfully to new forum topic")
                    except Exception as retry_error:
                        logger.error(f"❌ Failed to send retry: {type(retry_error).__name__}: {retry_error}")
                        raise
                else:
                    raise

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
