# 🎭 Anonka — Anonymous Telegram Bot

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-purple?style=flat-square)](LICENSE.md)
[![maintained](https://img.shields.io/badge/maintained%3F-yes-green?style=flat-square)](https://github.com/Mukller/Anonka)
[![contributions welcome](https://img.shields.io/badge/contributions-welcome-brightgreen?style=flat-square)](CONTRIBUTING.md)
[![Python](https://img.shields.io/badge/Python-3.12%2B-blue?style=flat-square&logo=python)](https://www.python.org/)

Русский • [English](README_EN.md)

</div>

Telegram bot for receiving anonymous messages with support for admin replies via private forum threads.

## 💡 How It Works

```
User                     Bot                    Admin Group (Forum)
  │                       │                              │
  │── /start ────────────►│                              │
  │                       │                              │
  │── "Hello!" ──────────►│── creates thread ───────────►│
  │                       │                              │
  │                       │── posts with button ────────►│
  │                       │   "💬 Reply"                  │
  │                       │                              │
  │                       │◄────── clicks button ─────────│
  │                       │                              │
  │                       │◄────── writes reply in DM ────│
  │                       │                              │
  │◄── reply in DM ───────│── posts in thread ──────────►│
```

## ✨ Features

- 📨 **Anonymous messages** — users send to DM, bot forwards to group
- 💬 **Admin replies** — admins reply via private forum threads
- 🔒 **Full anonymity** — user identities are never revealed
- 🗂️ **Forum threads** — each user gets their own thread in the admin group
- 🐳 **Docker support** — easy deployment with containerization
- 🗄️ **Database** — MySQL/PostgreSQL for persistent data storage

## 📦 Requirements

- Python 3.12+
- MySQL or PostgreSQL
- Docker and Docker Compose (optional)
- Telegram bot token (get from [@BotFather](https://t.me/BotFather))
- Telegram group with forum topics enabled

## 🚀 Installation

```bash
git clone https://github.com/Mukller/Anonka.git
cd Anonka
cp .env.example .env
# Edit .env with your settings
docker-compose up -d
```

## ⚙️ Configuration

See `.env.example` for all available configuration options.

## 🤝 Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines.

## 📄 License

This project is licensed under the MIT License — see [LICENSE.md](LICENSE.md) for details.

## 🔐 Security

See [SECURITY.md](SECURITY.md) for reporting vulnerabilities.
