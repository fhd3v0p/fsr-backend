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

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)  # Разрешаем CORS для Flutter Web App

# Путь к базе данных
DB_PATH = 'users.db'

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
        
        # Загрузки по категориям
        cursor.execute('''
            SELECT category, COUNT(*) 
            FROM photo_uploads 
            GROUP BY category
        ''')
        category_stats = dict(cursor.fetchall())
        
        # Загрузки за последние 7 дней
        cursor.execute('''
            SELECT COUNT(*) 
            FROM photo_uploads 
            WHERE created_at >= datetime('now', '-7 days')
        ''')
        recent_uploads = cursor.fetchone()[0]
        
        conn.close()
        
        return jsonify({
            'success': True,
            'stats': {
                'totalUploads': total_uploads,
                'categoryStats': category_stats,
                'recentUploads': recent_uploads
            }
        }), 200
        
    except Exception as e:
        logger.error(f"Error getting stats: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'}), 200

@app.route('/api/referral/<user_id>', methods=['GET'])
def get_referral_info(user_id):
    """Получение реферальной информации пользователя"""
    try:
        from database import Database
        db = Database()
        ref_info = db.get_user_referral_info(int(user_id))
        if ref_info:
            return jsonify(ref_info)
        else:
            return jsonify({'error': 'User not found'}), 404
    except Exception as e:
        logger.error(f"Error getting referral info: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/giveaway/prizes', methods=['GET'])
def get_giveaway_prizes():
    """Получение списка подарков гивевея"""
    try:
        from database import Database
        db = Database()
        prizes = db.get_giveaway_prizes()
        return jsonify(prizes)
    except Exception as e:
        logger.error(f"Error getting giveaway prizes: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/user/<user_id>/stats', methods=['GET'])
def get_user_stats(user_id):
    """Получение статистики пользователя"""
    try:
        from database import Database
        db = Database()
        stats = db.get_user_stats(int(user_id))
        if stats:
            return jsonify(stats)
        else:
            return jsonify({'error': 'User not found'}), 404
    except Exception as e:
        logger.error(f"Error getting user stats: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/create-prepared-message', methods=['POST'])
def create_prepared_message():
    """API endpoint для создания подготовленного сообщения для shareMessage"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Проверяем обязательные поля
        required_fields = ['title', 'description', 'message_text', 'user_id']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        # Генерируем простой ID сообщения
        message_id = f"invite_{data['user_id']}_{int(datetime.now().timestamp())}"
        
        logger.info(f"Prepared message created: user_id={data['user_id']}, message_id={message_id}")
        return jsonify({
            'success': True,
            'message_id': message_id
        }), 200
        
    except Exception as e:
        logger.error(f"Error creating prepared message: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/log-task-completion', methods=['POST'])
def log_task_completion():
    """API endpoint для логирования выполнения заданий"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        # Проверяем обязательные поля
        required_fields = ['user_id', 'task_name', 'task_number']
        for field in required_fields:
            if field not in data:
                return jsonify({'error': f'Missing required field: {field}'}), 400
        
        user_id = int(data['user_id'])
        task_name = data['task_name']
        task_number = int(data['task_number'])
        
        # Используем базу данных для логирования
        from database import Database
        db = Database()
        db.complete_task(user_id, task_name, task_number)
        
        logger.info(f"Task completed: user_id={user_id}, task={task_name}, number={task_number}")
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
        
        if 'user_id' not in data:
            return jsonify({'error': 'Missing user_id field'}), 400
        
        user_id = int(data['user_id'])
        
        # Используем базу данных для логирования
        from database import Database
        db = Database()
        db.log_referral_stats(user_id)
        
        logger.info(f"Referral stats logged: user_id={user_id}")
        return jsonify({
            'success': True,
            'message': 'Referral stats logged successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error logging referral stats: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/log-folder-subscription', methods=['POST'])
def log_folder_subscription():
    """API endpoint для логирования подписки на папку с каналами"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        if 'user_id' not in data:
            return jsonify({'error': 'Missing user_id field'}), 400
        
        user_id = int(data['user_id'])
        
        # Используем базу данных для логирования
        from database import Database
        db = Database()
        db.log_folder_subscription(user_id)
        
        logger.info(f"Folder subscription logged: user_id={user_id}")
        return jsonify({
            'success': True,
            'message': 'Folder subscription logged successfully'
        }), 200
        
    except Exception as e:
        logger.error(f"Error logging folder subscription: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/check-subscription', methods=['POST'])
def check_subscription():
    """Проверка подписки пользователя на все каналы из giveaway_channels"""
    try:
        data = request.get_json()
        user_id = int(data.get('user_id'))
        username = data.get('username')
        
        from database import Database
        db = Database()
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT channel_id FROM giveaway_channels')
        channels = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        bot = Bot(token=BOT_TOKEN)
        is_subscribed = False
        for channel_id in channels:
            try:
                member = asyncio.run(bot.get_chat_member(chat_id=channel_id, user_id=user_id))
                if member.status in ['member', 'administrator', 'creator']:
                    is_subscribed = True
                    break
            except Exception as e:
                continue
        return jsonify({'subscribed': is_subscribed}), 200
    except Exception as e:
        logger.error(f"Error checking subscription: {str(e)}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/user/<user_id>/tickets', methods=['GET'])
def get_user_tickets(user_id):
    """Получение количества билетов пользователя"""
    try:
        from database import Database
        db = Database()
        user_id = int(user_id)
        # Проверяем подписку
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute('SELECT channel_id FROM giveaway_channels')
        channels = [row[0] for row in cursor.fetchall()]
        conn.close()
        bot = Bot(token=BOT_TOKEN)
        is_subscribed = False
        for channel_id in channels:
            try:
                member = asyncio.run(bot.get_chat_member(chat_id=channel_id, user_id=user_id))
                if member.status in ['member', 'administrator', 'creator']:
                    is_subscribed = True
                    break
            except Exception:
                continue
        # Считаем друзей по рефке
        ref_info = db.get_user_referral_info(user_id)
        tickets = (1 if is_subscribed else 0) + (ref_info['successful_invites'] if ref_info else 0)
        username = db.get_user_stats(user_id).get('username', '')
        return jsonify({'tickets': tickets, 'subscribed': is_subscribed, 'username': username}), 200
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
        success = db.add_ticket_for_referral_start(inviter_id, invitee_id)
        tickets = db.get_user_tickets(inviter_id)
        return jsonify({'success': success, 'tickets': tickets}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Инициализируем таблицу при запуске
    init_photo_uploads_table()
    
    # Запускаем сервер
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=False
    ) 