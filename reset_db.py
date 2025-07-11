#!/usr/bin/env python3
"""
Скрипт для полной очистки всех пользовательских и реферальных данных в базе users.db
"""
import sqlite3
import os

DB_PATH = 'users.db'

def reset_database():
    if not os.path.exists(DB_PATH):
        print(f'Файл базы данных {DB_PATH} не найден!')
        return
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        print('Удаляем все данные из таблиц...')
        cursor.execute('DELETE FROM referral_invites;')
        cursor.execute('DELETE FROM giveaway_participants;')
        cursor.execute('DELETE FROM user_activity;')
        cursor.execute('DELETE FROM photo_uploads;')
        cursor.execute('DELETE FROM users;')
        conn.commit()
        print('✅ Все данные очищены!')
    except Exception as e:
        print(f'❌ Ошибка при очистке: {e}')
    finally:
        conn.close()

if __name__ == '__main__':
    reset_database() 