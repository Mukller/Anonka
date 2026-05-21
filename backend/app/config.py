import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROUP_CHAT_ID = int(os.getenv("GROUP_CHAT_ID", "0"))
GROUP_TOPIC_ID = int(os.getenv("GROUP_TOPIC_ID", "0")) or None

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_USER = os.getenv("DB_USER", "root")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")
DB_NAME = os.getenv("DB_NAME", "anonka")
DB_PORT = int(os.getenv("DB_PORT", "3306"))

DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN not set in .env")
if not GROUP_CHAT_ID:
    raise ValueError("GROUP_CHAT_ID not set in .env")
