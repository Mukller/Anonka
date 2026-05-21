# 🔐 Telegram Anonymous Thread Bot

Telegram бот для анонимной публикации сообщений в группе с возможностью владельца видеть отправителя и управлять сообщениями.

## ✨ Возможности

- 📨 Анонимная публикация сообщений в группу
- 🆔 Отображение username и времени отправки для владельца
- 💬 Возможность отвечать на сообщения
- ✏️ Редактирование сообщений
- 🗑️ Удаление сообщений
- 📎 Поддержка всех типов вложений
- 💾 Сохранение всех сообщений в MySQL

## 🚀 Быстрый старт

```bash
git clone https://github.com/Mukller/Anonka.git
cd Anonka
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Отредактируйте .env
cd backend
python init_db.py
python -m app.main
```

## 📋 Структура проекта

```
Anonka/
├── backend/
│   ├── app/
│   │   ├── models.py
│   │   ├── handlers.py
│   │   ├── main.py
│   ├── init_db.py
├── requirements.txt
├── .env.example
└── README.md
```

## 👤 Автор

Anton - https://github.com/Mukller
