import asyncio
import logging
import gc
import time
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand, WebAppInfo
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.enums import ParseMode
import os
from dotenv import load_dotenv
from database import Database
from logger import TelegramLogger

# Загружаем переменные окружения
load_dotenv()

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=os.getenv('BOT_TOKEN'))
dp = Dispatcher()

# Инициализация базы данных и логгера
db = Database()
telegram_logger = TelegramLogger()

# ID администраторов
admin_ids = [int(os.getenv('ADMIN_CHAT_ID', '0'))]

# Константы
WEBAPP_URL = 'https://FSR.agency'
GIVEAWAY_LINK = os.getenv('GIVEAWAY_LINK', 'https://t.me/addlist/f3YaeLmoNsdkYjVl')

# Функция для получения URL с версией для принудительного обновления кэша
def get_webapp_url_with_version():
    """Возвращает URL с версией для принудительного обновления кэша"""
    version = int(time.time())  # Используем timestamp как версию
    return f"{WEBAPP_URL}?v={version}"

# Команды бота для меню
async def set_bot_commands():
    """Установка команд бота в меню"""
    commands = [
        BotCommand(command="start", description="🚀 Запустить FSR"),
        BotCommand(command="giveaway", description="🎁 Розыгрыш призов"),
        BotCommand(command="invite", description="👥 Пригласить друзей"),
        BotCommand(command="help", description="❓ Справка"),
    ]
    
    if admin_ids[0] != 0:  # Если указан админ
        commands.append(BotCommand(command="stats", description="📊 Статистика (админ)"))
    
    await bot.set_my_commands(commands)

# Создание inline-кнопки для открытия Mini App
def get_webapp_keyboard() -> InlineKeyboardMarkup:
    """Создание inline-кнопки для открытия Mini App"""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="🌟 Open FSR",
            web_app=types.WebAppInfo(url=WEBAPP_URL)
        )
    )
    return builder.as_markup()

# Создание кнопки для гивевея
def get_giveaway_keyboard() -> InlineKeyboardMarkup:
    """Создание кнопки для гивевея"""
    builder = InlineKeyboardBuilder()
    builder.add(
        InlineKeyboardButton(
            text="📁 Подписаться на папку",
            url=GIVEAWAY_LINK
        )
    )
    builder.add(
        InlineKeyboardButton(
            text="🌟 Open FSR",
            web_app=types.WebAppInfo(url=WEBAPP_URL)
        )
    )
    return builder.as_markup()

@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    """Обработчик команды /start"""
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name
    
    # Проверяем, есть ли реферальный код в команде
    referred_by = None
    if len(message.text.split()) > 1:
        ref_code = message.text.split()[1]
        if ref_code.startswith('ref'):
            referred_by = ref_code[3:]  # Убираем 'ref' префикс
    
    # Добавляем пользователя в базу данных
    db.add_user(user_id, username, first_name, last_name, referred_by)
    
    # Если пользователь пришел по реферальной ссылке — начисляем билет пригласившему
    if referred_by:
        try:
            inviter_id = int(referred_by)
            invitee_id = user_id
            db.add_ticket_for_referral_start(inviter_id, invitee_id)
        except Exception as e:
            print(f"Error adding ticket for referral: {e}")
    
    # Логируем действие с информацией о реферале
    if referred_by:
        # Получаем информацию о пригласившем пользователе
        try:
            inviter_info = db.get_user_stats(int(referred_by))
            if inviter_info:
                inviter_username = inviter_info.get('username', 'без username')
                inviter_name = inviter_info.get('first_name', 'Неизвестно')
                inviter_id = inviter_info.get('user_id')
                ref_info_text = f"Приглашен пользователем: {inviter_name} (@{inviter_username}) ID: {inviter_id}"
            else:
                ref_info_text = f"Реферальный код: {referred_by} (пользователь не найден)"
        except Exception as e:
            ref_info_text = f"Реферальный код: {referred_by} (ошибка получения данных: {e})"
    else:
        ref_info_text = "Пришел без реферальной ссылки"
    
    asyncio.create_task(telegram_logger.log_user_action(
        user_id, username, first_name, "start", ref_info_text
    ))
    
    # Создаем клавиатуру
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text="🌟 Open FSR",
        web_app=WebAppInfo(url=WEBAPP_URL)
    ))
    builder.add(InlineKeyboardButton(
        text="📁 Подписаться на папку",
        url=GIVEAWAY_LINK
    ))
    
    welcome_text = f"""
🎉 Привет, {first_name or 'друг'}!

Добро пожаловать в **Fresh Style Russia** - платформу для поиска лучших артистов!

🎯 **Что у нас есть:**
• AI-поиск артистов по фото
• Каталог мастеров по городам
• Розыгрыш призов на 170,000₽
• Реферальная система с бонусами

🚀 Нажми "Open FSR" чтобы начать!
    """
    
    await message.answer(welcome_text, reply_markup=builder.as_markup(), parse_mode=ParseMode.MARKDOWN)

@dp.message(Command("giveaway"))
async def cmd_giveaway(message: types.Message):
    """Обработчик команды /giveaway"""
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    
    # Логируем действие
    asyncio.create_task(telegram_logger.log_user_action(
        user_id, username, first_name, "giveaway", "User requested giveaway info"
    ))
    
    # Получаем информацию о подарках
    prizes = db.get_giveaway_prizes()
    
    prizes_text = "🎁 **ПРИЗЫ ГИВЕВЕЯ:**\n\n"
    total_value = 0
    
    for prize in prizes:
        prizes_text += f"💎 **{prize['name']}**\n"
        prizes_text += f"└ {prize['description']}\n"
        prizes_text += f"└ 💰 Стоимость: {prize['value']:,}₽\n\n"
        total_value += prize['value']
    
    prizes_text += f"🏆 **ОБЩАЯ СТОИМОСТЬ ПРИЗОВ: {total_value:,}₽**\n\n"
    prizes_text += "🎯 **Как участвовать:**\n"
    prizes_text += "1️⃣ Подпишись на Telegram-папку\n"
    prizes_text += "2️⃣ Пригласи друзей\n"
    prizes_text += "3️⃣ Выполни все задания в приложении\n\n"
    prizes_text += "⏰ **Дедлайн:** 10 июля 2025, 20:00"
    
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text="📁 Подписаться на папку",
        url=GIVEAWAY_LINK
    ))
    builder.add(InlineKeyboardButton(
        text="🌟 Открыть приложение",
        web_app=WebAppInfo(url=WEBAPP_URL)
    ))
    # Удаляем кнопку Open FSR
    await message.answer(prizes_text, reply_markup=builder.as_markup(), parse_mode=ParseMode.MARKDOWN)

@dp.message(Command("invite"))
async def cmd_invite(message: types.Message):
    """Обработчик команды /invite для приглашения друзей"""
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    
    # Логируем действие
    asyncio.create_task(telegram_logger.log_user_action(
        user_id, username, first_name, "invite", "User requested invite friends"
    ))
    
    # Получаем реферальную информацию пользователя
    ref_info = db.get_user_referral_info(user_id)
    
    if not ref_info:
        await message.answer("❌ Ошибка получения реферальной информации")
        return
    
    # Создаем текст приглашения
    invite_text = f"""
🎯 **Пригласи друзей и получи бонусы!**

👥 **Твоя статистика:**
• Приглашено: {ref_info['successful_invites']} друзей
• Заработано XP: {ref_info['total_referral_xp']}
• Твой код: `{ref_info['referral_code']}`

🎁 **За каждого друга:**
• +100 XP тебе
• +100 XP другу
• Шанс выиграть призы

💬 **Текст для отправки друзьям:**
```
🔥 Привет! Нашел крутую платформу для поиска артистов - Fresh Style Russia!

🎯 Что тут есть:
• AI-поиск мастеров по фото
• Каталог артистов по городам  
• Розыгрыш на 170,000₽
• Бьюти-услуги и сертификаты

🎁 Присоединяйся по моей ссылке и получи бонусы:
{ref_info['referral_link']}

💎 Вместе выиграем призы! 🚀
```

📱 **Нажми кнопку ниже чтобы открыть диалог выбора друзей:**
    """
    
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text="👥 Пригласить друзей",
        web_app=WebAppInfo(url=f"{WEBAPP_URL}/invite?ref={ref_info['referral_code']}")
    ))
    builder.add(InlineKeyboardButton(
        text="📊 Моя статистика",
        callback_data="my_stats"
    ))
    
    await message.answer(invite_text, reply_markup=builder.as_markup(), parse_mode=ParseMode.MARKDOWN)

@dp.message(Command("stats"))
async def cmd_stats(message: types.Message):
    """Обработчик команды /stats (только для админов)"""
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    
    if user_id not in admin_ids:
        await message.answer("❌ У вас нет доступа к этой команде")
        return
    
    # Логируем действие
    asyncio.create_task(telegram_logger.log_user_action(
        user_id, username, first_name, "admin_stats", "Admin requested stats"
    ))
    
    # Получаем глобальную статистику
    global_stats = db.get_global_stats()
    
    stats_text = f"""
📊 **СТАТИСТИКА FSR БОТА**

👥 **Пользователи:**
• Всего: {global_stats.get('total_users', 0)}
• Активных за 7 дней: {global_stats.get('active_users_7d', 0)}
• Завершили гивевей: {global_stats.get('giveaway_completed', 0)}

📸 **Загрузки:**
• Всего фото: {global_stats.get('total_photos', 0)}

👥 **Рефералы:**
• Всего приглашений: {global_stats.get('total_referrals', 0)}

🎯 **Топ рефералов:**
{await get_top_referrers()}
    """
    
    await message.answer(stats_text, parse_mode=ParseMode.MARKDOWN)

@dp.message(Command("help"))
async def cmd_help(message: types.Message):
    """Обработчик команды /help"""
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    
    # Логируем действие
    asyncio.create_task(telegram_logger.log_user_action(
        user_id, username, first_name, "help", "User requested help"
    ))
    
    help_text = """
<b>🤖 FSR Bot - Справка</b>

<b>📋 Доступные команды:</b>
• <code>/start</code> - Запустить бота и открыть приложение
• <code>/giveaway</code> - Информация о розыгрыше призов
• <code>/invite</code> - Пригласить друзей и получить бонусы
• <code>/help</code> - Показать эту справку

<b>🎯 Как использовать:</b>
1. Нажми <b>Open FSR</b> чтобы открыть приложение
2. Выбери роль (клиент/артист)
3. Используй AI-поиск или каталог
4. Участвуй в гивевее и приглашай друзей

<b>🎁 Призы гивевея:</b>
• Сертификат Золотое Яблоко - 20,000₽
• Бьюти-услуги - 100,000₽
• Telegram Premium (3 мес) - 3,500₽
• <b>🏆 Общая стоимость призов: 123,500₽</b>

<b>🎫 Как получить билеты:</b>
• 1 билет — за подписку на Telegram-папку
• +1 билет — за каждого друга по реферальной ссылке

<b>💬 Поддержка:</b> @FSR_Adminka
    """
    
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text="🌟 Open FSR",
        web_app=WebAppInfo(url=WEBAPP_URL)
    ))
    
    await message.answer(help_text, reply_markup=builder.as_markup(), parse_mode=ParseMode.HTML)

@dp.callback_query(lambda c: c.data == "my_stats")
async def callback_my_stats(callback: types.CallbackQuery):
    """Обработчик кнопки 'Моя статистика'"""
    user_id = callback.from_user.id
    
    # Получаем статистику пользователя
    user_stats = db.get_user_stats(user_id)
    ref_info = db.get_user_referral_info(user_id)
    
    if not user_stats or not ref_info:
        await callback.answer("❌ Ошибка получения статистики")
        return
    
    stats_text = f"""
📊 **Твоя статистика**

👤 **Профиль:**
• Имя: {user_stats['first_name'] or 'Не указано'}
• Username: @{user_stats['username'] or 'Не указан'}
• Регистрация: {user_stats['registered_at'][:10]}

🎯 **Активность:**
• Заданий выполнено: {user_stats['tasks_completed']}
• Фото загружено: {user_stats['photos_uploaded']}
• Гивевей завершен: {'✅' if user_stats['giveaway_completed'] else '❌'}

👥 **Рефералы:**
• Приглашено друзей: {ref_info['successful_invites']}
• Заработано XP: {ref_info['total_referral_xp']}
• Реферальный код: `{ref_info['referral_code']}`

🎁 **Реферальная ссылка:**
`{ref_info['referral_link']}`
    """
    
    await callback.message.edit_text(stats_text, parse_mode=ParseMode.MARKDOWN)

async def get_top_referrers() -> str:
    """Получение топ рефералов"""
    try:
        conn = db.db_path
        import sqlite3
        conn = sqlite3.connect(conn)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT u.username, u.first_name, u.referral_count, u.total_referral_xp
            FROM users u
            WHERE u.referral_count > 0
            ORDER BY u.referral_count DESC, u.total_referral_xp DESC
            LIMIT 5
        ''')
        
        top_referrers = []
        for row in cursor.fetchall():
            username = row[0] or row[1] or "Unknown"
            top_referrers.append(f"• {username}: {row[2]} друзей, {row[3]} XP")
        
        conn.close()
        
        if top_referrers:
            return "\n".join(top_referrers)
        else:
            return "Пока нет рефералов"
            
    except Exception as e:
        print(f"Error getting top referrers: {e}")
        return "Ошибка получения данных"

# Новые методы для поддержки shareMessage
@dp.message(Command("save_message"))
async def cmd_save_message(message: types.Message):
    """Сохраняет подготовленное сообщение для отправки через Web App"""
    try:
        # Создаем inline query result для приглашения
        from aiogram.types import InlineQueryResultArticle, InputTextMessageContent
        
        result = InlineQueryResultArticle(
            id="invite_message",
            title="Приглашение в FSR",
            description="Пригласи друзей в Fresh Style Russia",
            input_message_content=InputTextMessageContent(
                message_text=f"""
🔥 <b>Привет! Нашел крутую платформу для поиска артистов - Fresh Style Russia!</b>

🎯 <b>Что тут есть:</b>
• AI-поиск мастеров по фото
• Каталог артистов по городам  
• Розыгрыш на 170,000₽
• Бьюти-услуги и сертификаты

🎁 <b>Присоединяйся по моей ссылке и получи бонусы:</b>
<a href="https://t.me/FSRUBOT?start=ref{message.from_user.id}">🚀 Открыть FSR</a>

💎 <b>Вместе выиграем призы!</b>

#FSR #FreshStyleRussia #Giveaway
                """,
                parse_mode=ParseMode.HTML
            )
        )
        
        # Сохраняем подготовленное сообщение
        prepared_message = await bot.save_prepared_inline_message(
            user_id=message.from_user.id,
            result=result,
            allow_user_chats=True,
            allow_bot_chats=False,
            allow_group_chats=True,
            allow_channel_chats=False
        )
        
        await message.answer(
            f"✅ Сообщение сохранено! ID: {prepared_message.id}\n"
            f"⏰ Истекает: {prepared_message.expiration_date}",
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        logger.error(f"Error saving prepared message: {e}")
        await message.answer("❌ Ошибка сохранения сообщения")

@dp.message(Command("test_share"))
async def cmd_test_share(message: types.Message):
    """Тестирует отправку сообщения через Web App"""
    try:
        # Создаем тестовое сообщение
        from aiogram.types import InlineQueryResultArticle, InputTextMessageContent
        
        result = InlineQueryResultArticle(
            id="test_invite",
            title="Тестовое приглашение",
            description="Тестовое сообщение для проверки shareMessage",
            input_message_content=InputTextMessageContent(
                message_text="🔥 Тестовое приглашение в FSR! 🚀",
                parse_mode=ParseMode.HTML
            )
        )
        
        # Сохраняем и сразу отправляем
        prepared_message = await bot.save_prepared_inline_message(
            user_id=message.from_user.id,
            result=result,
            allow_user_chats=True,
            allow_group_chats=True
        )
        
        await message.answer(
            f"✅ Тестовое сообщение готово!\n"
            f"ID: `{prepared_message.id}`\n\n"
            f"Теперь можно использовать shareMessage в Web App",
            parse_mode=ParseMode.MARKDOWN
        )
        
    except Exception as e:
        logger.error(f"Error in test share: {e}")
        await message.answer(f"❌ Ошибка: {str(e)}")

@dp.message()
async def handle_all_messages(message: types.Message):
    """Обработка всех остальных сообщений"""
    user_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    
    # Логируем действие пользователя
    asyncio.create_task(telegram_logger.log_user_action(
        user_id, username, first_name, "message_sent", f"User sent message: {message.text[:50]}{'...' if len(message.text) > 50 else ''}"
    ))
    
    await db.update_user_activity(user_id, "message_sent")
    
    # Очистка памяти каждые 100 сообщений для оптимизации
    if message.message_id % 100 == 0:
        gc.collect()
        logger.info(f"🧹 Очистка памяти выполнена (сообщение #{message.message_id})")
    
    # Отправляем кнопку для открытия Mini App
    await message.answer(
        "🌟 Нажмите кнопку, чтобы открыть FSR Mini App:",
        reply_markup=get_webapp_keyboard()
    )

async def check_bot_admin_status():
    channel_id = -1001973736826
    try:
        me = await bot.get_me()
        member = await bot.get_chat_member(chat_id=channel_id, user_id=me.id)
        if member.status in ['administrator', 'creator']:
            logger.info(f"✅ Бот является админом в канале {channel_id}")
        else:
            logger.error(f"❌ Бот НЕ админ в канале {channel_id}")
    except Exception as e:
        logger.error(f"❌ Ошибка проверки админства бота в канале {channel_id}: {e}")

async def main():
    """Основная функция"""
    logger.info("Запуск FSR Telegram Bot...")
    print("🚀 Запуск FSR Telegram Bot...")
    print(f"🌐 WebApp URL: {WEBAPP_URL}")
    print(f"📁 Giveaway Link: {GIVEAWAY_LINK}")
    print("=" * 50)

    # Проверка админства бота в канале
    await check_bot_admin_status()

    # Устанавливаем команды бота
    await set_bot_commands()

    # Логируем запуск бота в Telegram
    try:
        await telegram_logger.log_bot_start()
    except Exception as e:
        logger.error(f"Error logging bot start: {e}")
    
    # Запускаем бота
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main()) 