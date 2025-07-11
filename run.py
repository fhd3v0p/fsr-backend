#!/usr/bin/env python3
"""
Скрипт для запуска FSR Telegram Bot
"""

import sys
import os
import asyncio
import logging

# Добавляем текущую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

try:
    from bot import main
    from config import BOT_TOKEN
    
    # Проверяем токен
    if BOT_TOKEN == 'your_bot_token_here':
        print("❌ Ошибка: Не установлен токен бота!")
        print("📝 Создайте файл .env и добавьте BOT_TOKEN=ваш_токен")
        sys.exit(1)
    
    print("🚀 Запуск FSR Telegram Bot...")
    print(f"🌐 WebApp URL: https://FSR.agensy/")
    print(f"📁 Giveaway Link: https://t.me/addlist/f3YaeLmoNsdkYjVl")
    print("=" * 50)
    
    # Запускаем бота
    asyncio.run(main())
    
except ImportError as e:
    print(f"❌ Ошибка импорта: {e}")
    print("📦 Установите зависимости: pip install -r requirements.txt")
    sys.exit(1)
    
except KeyboardInterrupt:
    print("\n🛑 Бот остановлен пользователем")
    sys.exit(0)
    
except Exception as e:
    print(f"❌ Критическая ошибка: {e}")
    logging.error(f"Ошибка запуска бота: {e}")
    sys.exit(1) 