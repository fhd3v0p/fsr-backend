#!/usr/bin/env python3
"""
Скрипт для добавления тестовых данных в базу для проверки работы эндпоинтов
"""
import sqlite3
import os
from datetime import datetime

DB_PATH = 'users.db'

def add_test_data():
    if not os.path.exists(DB_PATH):
        print(f'Файл базы данных {DB_PATH} не найден!')
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        print('Добавляем тестовые данные...')
        
        # Добавляем тестовых пользователей
        test_users = [
            (123456789, 'test_user1', 'Test', 'User1', 'FSRABC123', None, 2),
            (987654321, 'test_user2', 'Test', 'User2', 'FSRDEF456', 'FSRABC123', 1),
            (555666777, 'test_user3', 'Test', 'User3', 'FSRGHI789', 'FSRABC123', 0),
        ]
        
        for user in test_users:
            cursor.execute('''
                INSERT OR REPLACE INTO users 
                (user_id, username, first_name, last_name, referral_code, referred_by, referral_count)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', user)
        
        # Добавляем участников гивевея
        participants = [123456789, 987654321, 555666777]
        for user_id in participants:
            cursor.execute('''
                INSERT OR REPLACE INTO giveaway_participants 
                (user_id, referral_code, tasks_completed, total_xp)
                VALUES (?, ?, ?, ?)
            ''', (user_id, f'FSR{user_id}', 1, 100))
        
        conn.commit()
        print('✅ Тестовые данные добавлены!')
        
        # Проверяем результат
        cursor.execute('SELECT COUNT(*) FROM users')
        users_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT COUNT(*) FROM giveaway_participants')
        participants_count = cursor.fetchone()[0]
        
        cursor.execute('SELECT SUM(referral_count) FROM users')
        total_referrals = cursor.fetchone()[0] or 0
        
        print(f'📊 Статистика:')
        print(f'   Пользователей: {users_count}')
        print(f'   Участников гивевея: {participants_count}')
        print(f'   Всего рефералов: {total_referrals}')
        print(f'   Ожидаемое количество билетов: {participants_count + total_referrals}')
        
    except Exception as e:
        print(f'❌ Ошибка при добавлении данных: {e}')
    finally:
        conn.close()

if __name__ == '__main__':
    add_test_data() 