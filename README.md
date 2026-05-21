# 🔐 Telegram Anonymous Thread Bot

Telegram бот для анонимной публикации сообщений в группе с функциями управления сообщениями.

## ✨ Возможности

- 📨 Анонимная публикация сообщений в группу
- 🆔 Отображение username и времени отправки для владельца
- 💬 Возможность отвечать на сообщения (в разработке)
- 🗑️ Удаление сообщений через кнопку
- 📎 Поддержка всех типов вложений (фото, видео, документы, аудио, голос)
- 💾 Сохранение всех сообщений в MySQL
- 🐳 Docker и Docker Compose поддержка

## 🚀 Быстрый старт

### Способ 1: Docker Compose (рекомендуется)

```bash
git clone https://github.com/Mukller/Anonka.git
cd Anonka
cp .env.example .env
# Отредактируйте .env с вашими данными
docker-compose up -d
```

### Способ 2: Ручная установка на сервер

```bash
# 1. Клонируем репо
git clone https://github.com/Mukller/Anonka.git
cd Anonka

# 2. Создаем виртуальное окружение
python3 -m venv venv
source venv/bin/activate  # На Windows: venv\Scripts\activate

# 3. Устанавливаем зависимости
pip install -r requirements.txt

# 4. Настраиваем переменные окружения
cp .env.example .env
nano .env  # Отредактируйте файл

# 5. Инициализируем БД
cd backend
python init_db.py

# 6. Запускаем бота
python -m app.main
```

### Способ 3: Развертывание на Linux сервер через systemd

```bash
# 1. Клонируем репо в /home/anton/anonka
git clone https://github.com/Mukller/Anonka.git /home/anton/anonka
cd /home/anton/anonka

# 2. Выполняем deploy скрипт
bash deploy.sh

# 3. Редактируем .env
nano .env

# 4. Запускаем сервис
systemctl start anonka

# 5. Проверяем статус
systemctl status anonka

# 6. Просматриваем логи
journalctl -u anonka -f
```

## 📋 Структура проекта

```
Anonka/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py          # Конфигурация
│   │   ├── models.py          # SQLAlchemy модели
│   │   ├── handlers.py        # Обработчики бота
│   │   ├── main.py            # Главное приложение
│   │   └── utils/
│   ├── init_db.py             # Инициализация БД
│   ├── migrations/
│   └── tests/
├── docker-compose.yml         # Docker Compose конфиг
├── Dockerfile                 # Docker образ
├── .env.example              # Пример переменных
├── anonka.service            # Systemd сервис
├── deploy.sh                 # Скрипт развертывания
├── requirements.txt          # Python зависимости
└── README.md
```

## 🗄️ База данных

### Таблицы

**users**
- `id` - ID пользователя
- `telegram_id` - Telegram ID
- `username` - Username в Telegram
- `created_at` - Дата создания

**threads**
- `id` - ID ветки
- `user_id` - ID пользователя (FK)
- `group_chat_id` - ID группы
- `topic_id` - ID топика в группе
- `created_at` - Дата создания

**messages**
- `id` - ID сообщения
- `thread_id` - ID ветки (FK)
- `sender_telegram_id` - Telegram ID отправителя
- `sender_username` - Username отправителя
- `message_text` - Текст сообщения
- `attachments` - JSON с вложениями
- `created_at` - Дата отправки

**responses**
- `id` - ID ответа
- `message_id` - ID сообщения (FK)
- `responder_user_id` - ID ответившего пользователя
- `response_text` - Текст ответа
- `attachments` - JSON с вложениями
- `created_at` - Дата ответа

## ⚙️ Конфигурация

### Переменные окружения (.env)

```env
# Telegram Bot
BOT_TOKEN=1234567890:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefg
GROUP_CHAT_ID=-1001234567890
GROUP_TOPIC_ID=0  # 0 для основной ветки группы

# MySQL Database
DB_HOST=localhost
DB_PORT=3306
DB_USER=root
DB_PASSWORD=your_secure_password
DB_NAME=anonka
```

## 📖 Получение необходимых ID

### Telegram Bot Token
1. Откройте [@BotFather](https://t.me/BotFather)
2. Отправьте `/newbot`
3. Следуйте инструкциям
4. Скопируйте полученный токен в `BOT_TOKEN`

### Group Chat ID
1. Добавьте бота в группу
2. Отправьте сообщение в группу
3. Откройте: `https://api.telegram.org/bot{TOKEN}/getUpdates`
4. Найдите `"chat":{"id":-1001234567890}` и скопируйте ID в `GROUP_CHAT_ID`

## 🔧 Разработка

### Запуск в режиме разработки

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

export BOT_TOKEN=your_token
export GROUP_CHAT_ID=your_chat_id
export DB_PASSWORD=your_password

cd backend
python -m app.main
```

### Добавление новых функций

1. Обновите модели в `backend/app/models.py`
2. Добавьте обработчики в `backend/app/handlers.py`
3. Создайте миграцию в `backend/migrations/`
4. Протестируйте локально
5. Создайте PR в GitHub

## 📊 Мониторинг

### Docker Compose
```bash
docker-compose logs -f bot
```

### Systemd
```bash
journalctl -u anonka -f
systemctl status anonka
```

## 🐛 Troubleshooting

### Бот не отвечает
```bash
# Проверьте token
python -c "from backend.app.config import BOT_TOKEN; print(f'Token: {BOT_TOKEN[:20]}...')"

# Проверьте подключение к БД
cd backend
python init_db.py
```

### Ошибки подключения к MySQL
```bash
# Проверьте учетные данные в .env
# Убедитесь что MySQL запущен
systemctl status mysql  # или docker ps
```

## 📝 Лицензия

MIT

## 👤 Автор

Anton - [GitHub](https://github.com/Mukller)

## 🤝 Контрибьютинг

Готовы помочь? Создавайте PR и issues!
