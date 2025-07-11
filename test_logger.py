#!/usr/bin/env python3
"""
Тестовый скрипт для проверки работы Telegram логгера
"""

import asyncio
import sys
import os

# Добавляем текущую директорию в путь
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from logger import TelegramLogger
from config import BOT_TOKEN

async def test_logger():
    """Тестирование логгера"""
    print("🧪 Тестирование Telegram логгера...")
    print(f"🔑 Токен бота: {BOT_TOKEN[:10]}...")
    
    try:
        # Создаем экземпляр логгера
        logger = TelegramLogger()
        
        # Тестируем отправку сообщения
        print("📤 Отправляем тестовое сообщение...")
        await logger.log_bot_start()
        
        # Тестируем логирование действия пользователя
        print("👤 Логируем действие пользователя...")
        await logger.log_user_action(
            user_id=123456789,
            username="test_user",
            first_name="Тестовый",
            action="test_action",
            additional_info="Тестовое сообщение от логгера"
        )
        
        # Тестируем логирование приглашения друга
        print("👥 Логируем приглашение друга...")
        await logger.log_friend_invitation(
            inviter_id=123456789,
            inviter_name="Пригласивший",
            invitee_id=987654321,
            invitee_name="Приглашенный",
            referral_code="FSR123456"
        )
        
        # Тестируем логирование выполнения задания
        print("✅ Логируем выполнение задания...")
        await logger.log_task_completion(
            user_id=123456789,
            username="test_user",
            first_name="Тестовый",
            task_name="Подписаться на папку",
            task_number=1
        )
        
        # Тестируем логирование завершения гивевея
        print("🏆 Логируем завершение гивевея...")
        await logger.log_giveaway_completion(
            user_id=123456789,
            username="test_user",
            first_name="Тестовый",
            total_xp=200
        )
        
        # Тестируем логирование реферальной статистики
        print("📊 Логируем реферальную статистику...")
        await logger.log_referral_stats(
            user_id=123456789,
            username="test_user",
            first_name="Тестовый",
            referral_count=5,
            total_xp=500
        )
        
        # Тестируем логирование подписки на папку
        print("📁 Логируем подписку на папку...")
        await logger.log_folder_subscription(
            user_id=123456789,
            username="test_user",
            first_name="Тестовый"
        )
        
        print("✅ Все тесты выполнены успешно!")
        
        # Закрываем соединение
        await logger.close()
        
    except Exception as e:
        print(f"❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_logger()) 