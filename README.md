<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-purple?style=flat-square)](LICENSE.md)
[![maintained](https://img.shields.io/badge/maintained%3F-yes-green?style=flat-square)](https://github.com/Mukller/Anonka)
[![contributions welcome](https://img.shields.io/badge/contributions-welcome-brightgreen?style=flat-square)](CONTRIBUTING.md)

### 🌐 Язык / Language

**Нажми, чтобы развернуть нужный язык · Click to expand your language**

</div>

<details open>
<summary><b>🇬🇧 English</b></summary>

<br>

# 🎭 Anonka — Anonymous Telegram Bot

[![Release](https://img.shields.io/github/v/release/Mukller/Anonka)](https://github.com/Mukller/Anonka/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)

A Telegram bot for receiving anonymous messages, with admin replies through private forum topics.

## 💡 How it works

```
User                         Bot                    Admin group (forum)
     │                        │                              │
     │── /start ─────────────►│                              │
     │                        │                              │
     │── "Hi!" ──────────────►│── creates a topic ──────────►│
     │                        │                              │
     │                        │── posts with a button ──────►│
     │                        │   "💬 Reply"                 │
     │                        │                              │
     │                        │◄────── clicks the button ────│
     │                        │                              │
     │                        │◄────── writes a reply in DM ─│
     │                        │                              │
     │◄── reply in DM ────────│── posts into the topic ─────►│
```

## ✨ Features

- 📨 **Anonymous messages** — users send DMs, the bot forwards them to the group
- 🧵 **Automatic forum topics** — each user gets their own topic
- 💬 **Two-way conversation** — admins reply, and the reply reaches the user
- 🔄 **Self-healing topics** — if a topic is deleted, the bot recreates it automatically (up to 3 attempts)
- ✅ **Proactive validation** — checks a topic exists before sending
- 📎 **All attachment types** — photos, videos, documents, audio, voice, animations
- 💾 **Stored in MySQL** — the whole conversation is kept in the DB
- 🤖 **Loop protection** — filters out messages from the bot itself
- 🚀 **Systemd service** — auto-start and restart on failure

## 🚀 Quick start

### Option 1: Systemd (recommended for production)

```bash
# 1. Clone
git clone https://github.com/Mukller/Anonka.git /home/anton/anonka
cd /home/anton/anonka

# 2. Create a venv and install dependencies
python3 -m venv venv
./venv/bin/pip install -r requirements.txt

# 3. Configure .env
cp .env.example .env
nano .env

# 4. Create the MySQL database and user
sudo mysql <<EOF
CREATE DATABASE anonka;
CREATE USER 'anonka'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON anonka.* TO 'anonka'@'localhost';
FLUSH PRIVILEGES;
EOF

# 5. Initialize the DB
./venv/bin/python backend/init_db.py

# 6. Install the systemd service
sudo cp anonka.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable anonka
sudo systemctl start anonka

# 7. View the logs
sudo journalctl -u anonka -f
```

### Option 2: Docker Compose

```bash
git clone https://github.com/Mukller/Anonka.git
cd Anonka
cp .env.example .env
# Edit .env
docker-compose up -d
docker-compose logs -f bot
```

### Option 3: Run manually (for development)

```bash
git clone https://github.com/Mukller/Anonka.git
cd Anonka
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Edit .env
python -m backend.app.main
```

## ⚙️ Configuration (.env)

```env
# Telegram Bot
BOT_TOKEN=1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefg
GROUP_CHAT_ID=-1001234567890
GROUP_TOPIC_ID=0

# MySQL
DB_HOST=localhost
DB_PORT=3306
DB_USER=anonka
DB_PASSWORD=your_secure_password
DB_NAME=anonka
```

### Where to get the values

| Variable | Where to find it |
|---|---|
| `BOT_TOKEN` | [@BotFather](https://t.me/BotFather) → `/newbot` |
| `GROUP_CHAT_ID` | Add the bot to the group → send a message → open `https://api.telegram.org/bot<TOKEN>/getUpdates` → find `"chat":{"id":-100...}` |
| `GROUP_TOPIC_ID` | Leave it `0` — the bot creates topics per user itself |

### Group requirements

1. The group must be a **forum** (enable "Topics" in settings)
2. The bot must be an **admin** with permissions to:
   - Manage topics
   - Send messages
   - Delete messages (optional)

## 📋 Project structure

```
Anonka/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py          # Loads .env
│   │   ├── models.py          # SQLAlchemy: User, Thread, Message, Response
│   │   ├── handlers.py        # Bot logic (start, message, callback)
│   │   ├── main.py            # Entry point + Dispatcher
│   │   └── utils/
│   ├── init_db.py             # Table creation
│   ├── migrations/
│   └── tests/
├── docker-compose.yml         # MySQL + bot containers
├── Dockerfile
├── anonka.service             # Systemd unit
├── deploy.sh                  # Deployment script
├── .env.example
├── requirements.txt
└── README.md
```

## 🗄️ Data model

```
User (telegram_id, username)
  └── Thread (group_chat_id, topic_id)
        └── Message (sender_telegram_id, text, attachments, created_at)
              └── Response (responder_user_id, text, attachments)
```

## 🔧 Topic-handling architecture

The bot uses a helper `ensure_forum_topic()` that guarantees a valid forum topic before sending:

```python
async def ensure_forum_topic(bot, db, thread, group_chat_id, topic_name, max_attempts=3):
    # 1. If topic_id exists — validate via reopen_forum_topic (no-op if alive)
    # 2. If the topic is invalid — reset topic_id and recreate it
    # 3. Up to 3 creation attempts with backoff 2s/4s/6s
    # 4. After creation — sleep 1.5s for Telegram to register it
```

This solves the **"message thread not found"** problem when:
- An admin deleted the topic manually
- The topic is archived/closed
- Telegram hasn't registered the new topic yet

## 📊 Monitoring

### Systemd
```bash
sudo systemctl status anonka       # Status
sudo journalctl -u anonka -f       # Live logs
sudo systemctl restart anonka      # Restart
```

### Docker
```bash
docker-compose ps
docker-compose logs -f bot
docker-compose restart bot
```

## 🐛 Troubleshooting

### `TelegramConflictError: terminated by other getUpdates request`
Multiple bot instances are running. Check:
```bash
ps aux | grep "python -m backend.app.main"
docker ps | grep anonka-bot
```
Keep only one instance.

### `message thread not found`
The topic was deleted in Telegram. **The bot recreates it itself** on the next message — nothing to do.

### `Access denied for user 'root'@'localhost'`
Use the dedicated MySQL user `anonka` instead of root:
```sql
CREATE USER 'anonka'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL ON anonka.* TO 'anonka'@'localhost';
```

### `ModuleNotFoundError: No module named 'aiogram'`
Run via the venv:
```bash
./venv/bin/python -m backend.app.main
# not
python -m backend.app.main
```

## 🛠️ Stack

- **Python 3.12+**
- **aiogram 3.x** — asynchronous Telegram Bot API
- **SQLAlchemy 2.x** + **PyMySQL** — ORM and MySQL driver
- **MySQL 8.0** — conversation storage
- **systemd** / **Docker Compose** — orchestration

## 📝 License

MIT

## 👤 Author

Anton — [@Mukller](https://github.com/Mukller)

## 🤝 Contributing

PRs and issues are welcome! See [issues](https://github.com/Mukller/Anonka/issues).

---

📦 **Latest release:** [v1.0.0](https://github.com/Mukller/Anonka/releases/tag/v1.0.0)

</details>

<details>
<summary><b>🇷🇺 Русский</b></summary>

<br>

# 🎭 Anonka — Анонимный Telegram бот

[![Release](https://img.shields.io/github/v/release/Mukller/Anonka)](https://github.com/Mukller/Anonka/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.12+](https://img.shields.io/badge/python-3.12+-blue.svg)](https://www.python.org/downloads/)

Telegram бот для приёма анонимных сообщений с поддержкой ответов от администраторов через приватные форум-темы.

## 💡 Как это работает

```
Пользователь                 Бот                    Админ-группа (форум)
     │                        │                              │
     │── /start ─────────────►│                              │
     │                        │                              │
     │── "Привет!" ──────────►│── создаёт тему ─────────────►│
     │                        │                              │
     │                        │── публикует с кнопкой ──────►│
     │                        │   "💬 Ответить"              │
     │                        │                              │
     │                        │◄────── нажимает кнопку ──────│
     │                        │                              │
     │                        │◄────── пишет ответ в ЛС ─────│
     │                        │                              │
     │◄── ответ в ЛС ─────────│── публикует в тему ─────────►│
```

## ✨ Возможности

- 📨 **Анонимные сообщения** — пользователи отправляют в ЛС, бот форвардит в группу
- 🧵 **Автоматические форум-темы** — каждый пользователь получает свою тему
- 💬 **Двусторонняя переписка** — админы отвечают, ответ доходит до пользователя
- 🔄 **Самовосстановление тем** — если тема удалена, бот автоматически создаст новую (до 3 попыток)
- ✅ **Проактивная валидация** — проверка существования темы перед отправкой
- 📎 **Все типы вложений** — фото, видео, документы, аудио, голосовые, анимации
- 💾 **Сохранение в MySQL** — вся переписка в БД для истории
- 🤖 **Защита от петель** — фильтр сообщений от самого бота
- 🚀 **Systemd сервис** — авто-старт и перезапуск при сбоях

## 🚀 Быстрый старт

### Вариант 1: Systemd (рекомендуется для production)

```bash
# 1. Клонируем
git clone https://github.com/Mukller/Anonka.git /home/anton/anonka
cd /home/anton/anonka

# 2. Создаём venv и ставим зависимости
python3 -m venv venv
./venv/bin/pip install -r requirements.txt

# 3. Настраиваем .env
cp .env.example .env
nano .env

# 4. Создаём БД и пользователя MySQL
sudo mysql <<EOF
CREATE DATABASE anonka;
CREATE USER 'anonka'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON anonka.* TO 'anonka'@'localhost';
FLUSH PRIVILEGES;
EOF

# 5. Инициализируем БД
./venv/bin/python backend/init_db.py

# 6. Устанавливаем systemd сервис
sudo cp anonka.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable anonka
sudo systemctl start anonka

# 7. Смотрим логи
sudo journalctl -u anonka -f
```

### Вариант 2: Docker Compose

```bash
git clone https://github.com/Mukller/Anonka.git
cd Anonka
cp .env.example .env
# Отредактируйте .env
docker-compose up -d
docker-compose logs -f bot
```

### Вариант 3: Запуск вручную (для разработки)

```bash
git clone https://github.com/Mukller/Anonka.git
cd Anonka
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Отредактируйте .env
python -m backend.app.main
```

## ⚙️ Конфигурация (.env)

```env
# Telegram Bot
BOT_TOKEN=1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefg
GROUP_CHAT_ID=-1001234567890
GROUP_TOPIC_ID=0

# MySQL
DB_HOST=localhost
DB_PORT=3306
DB_USER=anonka
DB_PASSWORD=your_secure_password
DB_NAME=anonka
```

### Где взять значения

| Переменная | Где найти |
|---|---|
| `BOT_TOKEN` | [@BotFather](https://t.me/BotFather) → `/newbot` |
| `GROUP_CHAT_ID` | Добавь бота в группу → отправь сообщение → открой `https://api.telegram.org/bot<TOKEN>/getUpdates` → найди `"chat":{"id":-100...}` |
| `GROUP_TOPIC_ID` | Оставь `0` — бот сам создаст темы для каждого пользователя |

### Требования к группе

1. Группа должна быть **форумом** (включи "Темы" в настройках)
2. Бот должен быть **админом** с правами:
   - Управление темами
   - Отправка сообщений
   - Удаление сообщений (опционально)

## 📋 Структура проекта

```
Anonka/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py          # Загрузка .env
│   │   ├── models.py          # SQLAlchemy: User, Thread, Message, Response
│   │   ├── handlers.py        # Логика бота (start, message, callback)
│   │   ├── main.py            # Точка входа + Dispatcher
│   │   └── utils/
│   ├── init_db.py             # Создание таблиц
│   ├── migrations/
│   └── tests/
├── docker-compose.yml         # MySQL + bot контейнеры
├── Dockerfile
├── anonka.service             # Systemd unit
├── deploy.sh                  # Скрипт развёртывания
├── .env.example
├── requirements.txt
└── README.md
```

## 🗄️ Модель данных

```
User (telegram_id, username)
  └── Thread (group_chat_id, topic_id)
        └── Message (sender_telegram_id, text, attachments, created_at)
              └── Response (responder_user_id, text, attachments)
```

## 🔧 Архитектура работы с темами

Бот использует helper-функцию `ensure_forum_topic()`, которая гарантирует наличие валидной форум-темы перед отправкой:

```python
async def ensure_forum_topic(bot, db, thread, group_chat_id, topic_name, max_attempts=3):
    # 1. Если topic_id есть — валидируем через reopen_forum_topic (no-op если жива)
    # 2. Если тема невалидна — обнуляем topic_id и создаём заново
    # 3. До 3 попыток создания с backoff 2с/4с/6с
    # 4. После создания — sleep 1.5с для регистрации в Telegram
```

Это решает проблему **"message thread not found"** когда:
- Админ удалил тему вручную
- Тема архивирована/закрыта
- Telegram не успел зарегистрировать новую тему

## 📊 Мониторинг

### Systemd
```bash
sudo systemctl status anonka       # Статус
sudo journalctl -u anonka -f       # Логи в реальном времени
sudo systemctl restart anonka      # Перезапуск
```

### Docker
```bash
docker-compose ps
docker-compose logs -f bot
docker-compose restart bot
```

## 🐛 Troubleshooting

### `TelegramConflictError: terminated by other getUpdates request`
Запущено несколько экземпляров бота. Проверь:
```bash
ps aux | grep "python -m backend.app.main"
docker ps | grep anonka-bot
```
Оставь только один экземпляр.

### `message thread not found`
Тема удалена в Telegram. **Бот сам её пересоздаст** на следующем сообщении — ничего делать не надо.

### `Access denied for user 'root'@'localhost'`
Используй отдельного MySQL юзера `anonka` вместо root:
```sql
CREATE USER 'anonka'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL ON anonka.* TO 'anonka'@'localhost';
```

### `ModuleNotFoundError: No module named 'aiogram'`
Запускай через venv:
```bash
./venv/bin/python -m backend.app.main
# а не
python -m backend.app.main
```

## 🛠️ Стек

- **Python 3.12+**
- **aiogram 3.x** — асинхронный Telegram Bot API
- **SQLAlchemy 2.x** + **PyMySQL** — ORM и MySQL драйвер
- **MySQL 8.0** — хранение переписки
- **systemd** / **Docker Compose** — оркестрация

## 📝 Лицензия

MIT

## 👤 Автор

Anton — [@Mukller](https://github.com/Mukller)

## 🤝 Контрибьютинг

PR и issues приветствуются! См. [issues](https://github.com/Mukller/Anonka/issues).

---

📦 **Последний релиз:** [v1.0.0](https://github.com/Mukller/Anonka/releases/tag/v1.0.0)

</details>
