from flask import Flask, request, jsonify
from flask_cors import CORS
import sqlite3
import json
import os
import base64
from datetime import datetime
import logging
import asyncio
from aiogram import Bot
from config import BOT_TOKEN
import threading
import time

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Разрешаем CORS для Flutter Web App

# Путь к базе данных
DB_PATH = 'fsr.db'

# Загрузка каналов из channels.json
with open('channels.json', 'r') as f:
    CHANNEL_IDS = json.load(f)['channels']

# Проверка, что бот админ во всех каналах при старте
async def check_bot_admin_rights():
    bot = Bot(token=BOT_TOKEN)
    me = await bot.me
    for channel_id in CHANNEL_IDS:
        try:
            member = await bot.get_chat_member(chat_id=channel_id, user_id=me.id)
            if member.status not in ['administrator', 'creator']:
                logger.error(f"Bot is NOT admin in channel {channel_id}!")
            else:
                logger.info(f"Bot is admin in channel {channel_id}")
        except Exception as e:
            logger.error(f"Error checking admin rights in channel {channel_id}: {e}")

def init_photo_uploads_table():
    """Инициализация таблицы для загруженных фото"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS photo_uploads (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            category TEXT NOT NULL,
            file_id TEXT NOT NULL,
            file_name TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            mime_type TEXT NOT NULL,
            upload_date TEXT NOT NULL,
            description TEXT,
            file_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

@app.route('/api/upload-photo', methods=['POST'])
def upload_photo():
    """API endpoint для загрузки фото"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Проверяем обязательные поля
        required_fields = ['id', 'userId', 'category', 'fileId', 'fileName', 'fileSize', 'mimeType', 'uploadDate']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Проверяем тип файла
        mime_type = data['mimeType']
        if not (mime_type.startswith('image/') or mime_type.startswith('video/')):
            return jsonify({'error': 'Only image and video files are allowed'}), 400
        
        # Проверяем размер файла (максимум 10MB)
        file_size = data['fileSize']
        if file_size > 10 * 1024 * 1024:  # 10MB
            return jsonify({'error': 'File size too large. Maximum size: 10MB'}), 400
        
        # Сохраняем в базу данных
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO photo_uploads 
            (id, user_id, category, file_id, file_name, file_size, mime_type, upload_date, description, file_data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            data['id'],
            data['userId'],
            data['category'],
            data['fileId'],
            data['fileName'],
            data['fileSize'],
            data['mimeType'],
            data['uploadDate'],
            data.get('description'),
            data.get('base64_data', ''),  # Сохраняем base64 данные файла
        ))
        
        conn.commit()
        conn.close()
        
        # Логируем успешную загрузку
        logger.info(f"Photo uploaded successfully: user_id={data['userId']}, category={data['category']}, file={data['fileName']}")
        
        return jsonify({
            'success': True,
            'message': 'Photo uploaded successfully',
            'photo_id': data['id']
        }), 200
        
    except Exception as e:
        logger.error(f"Error uploading photo: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/user-photos/<user_id>', methods=['GET'])
def get_user_photos(user_id):
    """API endpoint для получения фото пользователя"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, category, file_name, file_size, mime_type, upload_date, description
            FROM photo_uploads 
            WHERE user_id = ?
            ORDER BY upload_date DESC
        ''', (user_id,))
        
        photos = []
        for row in cursor.fetchall():
            photos.append({
                'id': row[0],
                'category': row[1],
                'fileName': row[2],
                'fileSize': row[3],
                'mimeType': row[4],
                'uploadDate': row[5],
                'description': row[6]
            })
        
        conn.close()
        
        return jsonify({
            'success': True,
            'photos': photos
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting user photos: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/photo/<photo_id>', methods=['GET'])
def get_photo(photo_id):
    """API endpoint для получения конкретного фото"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT file_data, mime_type, file_name
            FROM photo_uploads 
            WHERE id = ?
        ''', (photo_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return jsonify({'error': 'Photo not found'}), 404
        
        file_data, mime_type, file_name = row
        
        return jsonify({
            'success': True,
            'fileData': file_data,
            'mimeType': mime_type,
            'fileName': file_name
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting photo: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/delete-photo/<photo_id>', methods=['DELETE'])
def delete_photo(photo_id):
    """API endpoint для удаления фото"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM photo_uploads WHERE id = ?', (photo_id,))
        
        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'error': 'Photo not found'}), 404
        
        conn.commit()
        conn.close()
        
        logger.info(f"Photo deleted successfully: photo_id={photo_id}")
        
        return jsonify({
            'success': True,
            'message': 'Photo deleted successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error deleting photo: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/stats', methods=['GET'])
def get_stats():
    """API endpoint для получения статистики загрузок"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Общее количество загрузок
        cursor.execute('SELECT COUNT(*) FROM photo_uploads')
        total_uploads = cursor.fetchone()[0]
        
        # Количество уникальных пользователей
        cursor.execute('SELECT COUNT(DISTINCT user_id) FROM photo_uploads')
        unique_users = cursor.fetchone()[0]
        
        # Статистика по категориям
        cursor.execute('''
            SELECT category, COUNT(*) as count
            FROM photo_uploads
            GROUP BY category
            ORDER BY count DESC
        ''')
        
        category_stats = {}
        for row in cursor.fetchall():
            category_stats[row[0]] = row[1]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'stats': {
                'total_uploads': total_uploads,
                'unique_users': unique_users,
                'category_stats': category_stats
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'ok'}), 200

@app.route('/api/referral/<user_id>', methods=['GET'])
def get_referral_info(user_id):
    """API endpoint для получения реферальной информации пользователя"""
    try:
        from database import Database
        db = Database()
        user_id = int(user_id)
        ref_info = db.get_user_referral_info(user_id)
        return jsonify(ref_info), 200
    except Exception as e:
        logger.error(f"Error getting referral info: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/giveaway/prizes', methods=['GET'])
def get_giveaway_prizes():
    """API endpoint для получения призов гивевея"""
    try:
        from database import Database
        db = Database()
        prizes = db.get_giveaway_prizes()
        return jsonify({'prizes': prizes}), 200
    except Exception as e:
        logger.error(f"Error getting giveaway prizes: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/user/<user_id>/stats', methods=['GET'])
def get_user_stats(user_id):
    """API endpoint для получения статистики пользователя"""
    try:
        from database import Database
        db = Database()
        user_id = int(user_id)
        stats = db.get_user_stats(user_id)
        return jsonify(stats), 200
    except Exception as e:
        logger.error(f"Error getting user stats: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/create-prepared-message', methods=['POST'])
def create_prepared_message():
    """API endpoint для создания подготовленного сообщения"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        user_id = int(data.get('user_id'))
        message_type = data.get('message_type', 'default')
        
        from database import Database
        db = Database()
        
        # Логируем активность
        db.add_activity(user_id, f"create_message_{message_type}")
        
        return jsonify({
            'success': True,
            'message': 'Message created successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error creating prepared message: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/log-task-completion', methods=['POST'])
def log_task_completion():
    """API endpoint для логирования выполнения задания"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        user_id = int(data.get('user_id'))
        task_name = data.get('task_name')
        task_number = int(data.get('task_number', 1))
        
        from database import Database
        db = Database()
        
        # Логируем выполнение задания
        db.complete_task(user_id, task_name, task_number)
        
        return jsonify({
            'success': True,
            'message': 'Task completion logged successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error logging task completion: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/log-referral-stats', methods=['POST'])
def log_referral_stats():
    """API endpoint для логирования реферальной статистики"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        user_id = int(data.get('user_id'))
        
        from database import Database
        db = Database()
        
        # Логируем реферальную статистику
        db.log_referral_stats(user_id)
        
        return jsonify({
            'success': True,
            'message': 'Referral stats logged successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error logging referral stats: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

def async_check_and_award_ticket(user_id):
    """Асинхронная проверка подписки и начисление билета"""
    time.sleep(3)  # Дать время на подписку
    from database import Database
    db = Database()
    bot = Bot(token=BOT_TOKEN)
    
    # Проверяем подписку на все каналы
    all_subscribed = True
    for channel_id in CHANNEL_IDS:
        try:
            member = asyncio.run(bot.get_chat_member(chat_id=channel_id, user_id=user_id))
            if member.status not in ['member', 'administrator', 'creator']:
                all_subscribed = False
                break
        except Exception:
            all_subscribed = False
            break
    
    # Обновляем статус подписки в новой системе
    db.set_subscription_status(user_id, all_subscribed)
    
    if all_subscribed:
        logger.info(f"User {user_id} подписан на все каналы, статус обновлен!")
    else:
        logger.info(f"User {user_id} не подписан на все каналы, статус обновлен.")

@app.route('/api/log-folder-subscription', methods=['POST'])
def log_folder_subscription():
    """API endpoint для логирования подписки на папку с каналами и автоматической проверки подписки"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        if 'user_id' not in data:
            return jsonify({'error': 'Missing user_id field'}), 400
        user_id = int(data['user_id'])
        from database import Database
        db = Database()
        db.log_folder_subscription(user_id)
        logger.info(f"Folder subscription logged: user_id={user_id}")
        # Асинхронно проверяем подписку и обновляем статус
        threading.Thread(target=async_check_and_award_ticket, args=(user_id,)).start()
        return jsonify({
            'success': True,
            'message': 'Folder subscription logged successfully, checking subscription in background.'
        }), 200
    except Exception as e:
        logger.error(f"Error logging folder subscription: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/check-subscription', methods=['POST'])
def check_subscription():
    """Проверка подписки пользователя на все каналы из channels.json"""
    try:
        data = request.get_json()
        user_id = int(data.get('user_id'))
        bot = Bot(token=BOT_TOKEN)
        all_subscribed = True
        for channel_id in CHANNEL_IDS:
            try:
                member = asyncio.run(bot.get_chat_member(chat_id=channel_id, user_id=user_id))
                if member.status not in ['member', 'administrator', 'creator']:
                    all_subscribed = False
                    break
            except Exception:
                all_subscribed = False
                break
        
        # Обновляем статус в базе данных
        from database import Database
        db = Database()
        db.set_subscription_status(user_id, all_subscribed)
        
        return jsonify({'subscribed': all_subscribed}), 200
    except Exception as e:
        logger.error(f"Error checking subscription: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/user/<user_id>/tickets', methods=['GET'])
def get_user_tickets(user_id):
    """Получение количества билетов пользователя и статусов заданий"""
    try:
        from database import Database
        db = Database()
        user_id = int(user_id)
        
        # Используем новый метод для получения билетов
        tickets = db.get_user_tickets(user_id)
        
        # Получаем информацию о пользователе
        user_stats = db.get_user_stats(user_id)
        username = user_stats.get('username', '')
        
        # Получаем статусы заданий
        task_statuses = db.get_task_statuses(user_id)
        
        # Проверяем текущий статус подписки
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT is_subscribed_all FROM tickets_subscription WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        subscribed = result[0] if result else False
        conn.close()
        
        return jsonify({
            'tickets': tickets,
            'subscribed': subscribed,
            'username': username,
            'task1_done': task_statuses['task1_done'],
            'task2_done': task_statuses['task2_done']
        }), 200
    except Exception as e:
        logger.error(f"Error getting user tickets: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/check-subscription-by-username', methods=['POST'])
def check_subscription_by_username():
    """Проверка подписки пользователя на канал по username"""
    try:
        data = request.get_json()
        username = data.get('username')
        channel_id = -1001973736826  # Пример: один канал
        from aiogram import Bot
        from config import BOT_TOKEN
        bot = Bot(token=BOT_TOKEN)
        # Проверяем, что бот админ в канале
        try:
            bot_id = asyncio.run(bot.me).id
            member = asyncio.run(bot.get_chat_member(chat_id=channel_id, user_id=bot_id))
            if member.status not in ['administrator', 'creator']:
                return jsonify({'error': 'Bot is not admin in channel', 'admin': False}), 403
        except Exception as e:
            return jsonify({'error': f'Bot admin check failed: {e}', 'admin': False}), 500
        # Проверяем подписку пользователя по username
        try:
            # В реальности Telegram API не позволяет искать по username напрямую,
            # нужен user_id. Здесь пример: ищем среди админов по username.
            admins = asyncio.run(bot.get_chat_administrators(channel_id))
            found = False
            for admin in admins:
                if admin.user.username and admin.user.username.lower() == username.lower():
                    found = True
                    break
            return jsonify({'subscribed': found, 'admin': True}), 200
        except Exception as e:
            return jsonify({'error': f'User check failed: {e}', 'admin': True}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/add-ticket-for-referral', methods=['POST'])
def add_ticket_for_referral():
    """API endpoint для начисления билета пригласившему, если друг стартует по реф-ссылке"""
    try:
        data = request.get_json()
        inviter_id = int(data.get('inviter_id'))
        invitee_id = int(data.get('invitee_id'))
        from database import Database
        db = Database()
        
        # Используем новый метод для добавления билета за реферала
        db.add_referral_ticket(inviter_id, invitee_id)
        
        # Получаем обновленное количество билетов
        tickets = db.get_user_tickets(inviter_id)
        
        return jsonify({'success': True, 'tickets': tickets}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/tickets/total', methods=['GET'])
def get_total_tickets():
    """Получение общего количества билетов"""
    try:
        from database import Database
        db = Database()
        
        # Используем новую логику подсчета билетов
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Билеты за подписку на все каналы
        cursor.execute('SELECT COUNT(*) FROM tickets_subscription WHERE is_subscribed_all = 1')
        subscription_tickets = cursor.fetchone()[0]
        
        # Билеты за рефералов
        cursor.execute('SELECT COUNT(*) FROM tickets_referral')
        referral_tickets = cursor.fetchone()[0]
        
        conn.close()
        
        total = subscription_tickets + referral_tickets
        
        logger.info(f"Total tickets requested: {total} (subscription: {subscription_tickets}, referrals: {referral_tickets})")
        
        return jsonify({'total': total}), 200
        
    except Exception as e:
        logger.error(f"Error getting total tickets: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'}), 200

if __name__ == '__main__':
    # Инициализируем таблицу при запуске
    init_photo_uploads_table()
    # Проверяем админство бота во всех каналах
    asyncio.run(check_bot_admin_rights())
    # Запускаем сервер
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False
    ) 
