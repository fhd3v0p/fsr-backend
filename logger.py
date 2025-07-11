import asyncio
from datetime import datetime
from typing import Optional
from aiogram import Bot
from config import BOT_TOKEN

class TelegramLogger:
    def __init__(self, chat_id: int = -4948669471):
        self.chat_id = chat_id
        self.bot = Bot(token=BOT_TOKEN)
    
    async def log_user_action(self, user_id: int, username: Optional[str], 
                            first_name: Optional[str], action: str, 
                            additional_info: str = "") -> None:
        """Логирование действий пользователя"""
        try:
            timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            
            # Форматируем сообщение
            message = f"""
🆔 Лог действия пользователя

👤 Пользователь:
• ID: {user_id}
• Username: @{username or 'Не указан'}
• Имя: {first_name or 'Не указано'}

⚡ Действие: {action}
🕐 Время: {timestamp}

{additional_info}
            """.strip()
            
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=None
            )
        except Exception as e:
            print(f"Ошибка логирования: {e}")
    
    async def log_bot_start(self) -> None:
        """Логирование запуска бота"""
        try:
            timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            message = f"""
🚀 **Бот запущен!**

🆔 **Bot ID:** 8164568741
📝 **Название:** FRESH STYLE RUSSIA
🕐 **Время запуска:** {timestamp}
🌐 **WebApp URL:** https://FSR.agensy/

✅ **Бот готов к работе!**
            """.strip()
            
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"Ошибка логирования запуска: {e}")
    
    async def log_database_action(self, user_id: int, action: str, 
                                success: bool, details: str = "") -> None:
        """Логирование действий с базой данных"""
        try:
            timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            status = "✅ Успешно" if success else "❌ Ошибка"
            
            message = f"""
🗄️ **Действие с базой данных**

👤 **Пользователь ID:** `{user_id}`
⚡ **Действие:** {action}
📊 **Статус:** {status}
🕐 **Время:** {timestamp}

📝 **Детали:** {details}
            """.strip()
            
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"Ошибка логирования БД: {e}")
    
    async def log_error(self, error: str, context: str = "") -> None:
        """Логирование ошибок"""
        try:
            timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            
            message = f"""
⚠️ **Ошибка в боте**

❌ **Ошибка:** {error}
📋 **Контекст:** {context}
🕐 **Время:** {timestamp}
            """.strip()
            
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"Ошибка логирования ошибки: {e}")
    
    async def log_statistics(self, stats: dict) -> None:
        """Логирование статистики"""
        try:
            timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            
            message = f"""
📊 **Статистика FSR Bot**

👥 **Всего пользователей:** {stats.get('total_users', 0)}
✅ **Завершили гивевей:** {stats.get('completed_giveaway', 0)}
🔥 **Активных за 7 дней:** {stats.get('active_users_7d', 0)}
🕐 **Время:** {timestamp}
            """.strip()
            
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"Ошибка логирования статистики: {e}")
    
    async def log_friend_invitation(self, inviter_id: int, inviter_name: str, 
                                  invitee_id: int, invitee_name: str, referral_code: str) -> None:
        """Логирование приглашения друга"""
        try:
            timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            
            message = f"""
👥 Приглашение друга!

🎯 Пригласивший:
• ID: {inviter_id}
• Имя: {inviter_name}

👤 Приглашенный:
• ID: {invitee_id}
• Имя: {invitee_name}

🔗 Реферальный код: {referral_code}

🎁 Бонусы:
• +100 XP пригласившему
• +100 XP приглашенному

🕐 Время: {timestamp}
            """.strip()
            
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=None
            )
        except Exception as e:
            print(f"Ошибка логирования приглашения: {e}")
    
    async def log_task_completion(self, user_id: int, username: str, 
                                first_name: str, task_name: str, 
                                task_number: int) -> None:
        """Логирование выполнения задания"""
        try:
            timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            
            message = f"""
✅ Задание выполнено!

👤 Пользователь:
• ID: {user_id}
• Username: @{username or 'Не указан'}
• Имя: {first_name}

📋 Задание: {task_name}
🔢 Номер: {task_number}/2

🎯 Прогресс: {task_number}/2 заданий выполнено

🕐 Время: {timestamp}
            """.strip()
            
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=None
            )
        except Exception as e:
            print(f"Ошибка логирования выполнения задания: {e}")
    
    async def log_giveaway_completion(self, user_id: int, username: str, 
                                    first_name: str, total_xp: int) -> None:
        """Логирование завершения гивевея"""
        try:
            timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            
            message = f"""
🏆 Гивевей завершен!

👤 Пользователь:
• ID: {user_id}
• Username: @{username or 'Не указан'}
• Имя: {first_name}

🎁 Результат:
• Все задания выполнены ✅
• Заработано XP: {total_xp}
• Участвует в розыгрыше призов!

🎯 Призы:
• Сертификат в ZARA - 20,000₽
• Бьюти-услуги - 100,000₽  
• VIP-статус - 50,000₽

🕐 Время: {timestamp}
            """.strip()
            
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=None
            )
        except Exception as e:
            print(f"Ошибка логирования завершения гивевея: {e}")
    
    async def log_referral_stats(self, user_id: int, username: str, 
                               first_name: str, referral_count: int, 
                               total_xp: int) -> None:
        """Логирование реферальной статистики"""
        try:
            timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            
            message = f"""
👥 Реферальная статистика

👤 Пользователь:
• ID: {user_id}
• Username: @{username or 'Не указан'}
• Имя: {first_name}

📊 Статистика:
• Приглашено друзей: {referral_count}
• Заработано XP: {total_xp}

🎁 Бонусы за приглашения:
• +100 XP за каждого друга
• Шанс выиграть призы

🕐 Время: {timestamp}
            """.strip()
            
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=None
            )
        except Exception as e:
            print(f"Ошибка логирования реферальной статистики: {e}")
    
    async def log_folder_subscription(self, user_id: int, username: str, 
                                    first_name: str) -> None:
        """Логирование подписки на папку с каналами"""
        try:
            timestamp = datetime.now().strftime("%d.%m.%Y %H:%M:%S")
            
            message = f"""
📁 Подписка на папку с каналами!

👤 Пользователь:
• ID: {user_id}
• Username: @{username or 'Не указан'}
• Имя: {first_name}

🎯 Действие: Подписался на Telegram-папку
📋 Содержимое: 10 каналов Fresh Style Russia
🎁 Бонус: +1000 XP за подписку

🕐 Время: {timestamp}
            """.strip()
            
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=None
            )
        except Exception as e:
            print(f"Ошибка логирования подписки на папку: {e}")
    
    async def close(self):
        """Закрытие соединения с ботом"""
        await self.bot.session.close()

# Создаем глобальный экземпляр логгера
telegram_logger = TelegramLogger() 