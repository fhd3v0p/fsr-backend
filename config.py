import os
from dotenv import load_dotenv

# Загружаем переменные окружения из .env файла
load_dotenv()

# Telegram Bot Token (получите у @BotFather)
BOT_TOKEN = os.getenv('BOT_TOKEN', 'your_bot_token_here')

# Web App URL (ваш Flutter web app)
WEBAPP_URL = os.getenv('WEBAPP_URL', 'https://FSR.agensy/')

# Database path
DATABASE_PATH = os.getenv('DATABASE_PATH', 'users.db')

# Giveaway folder link
GIVEAWAY_FOLDER_LINK = 'https://t.me/addlist/f3YaeLmoNsdkYjVl' 