#!/usr/bin/env python3
"""
Скрипт для принудительной инициализации базы данных
"""

import os
import sqlite3

def force_init_database():
    """Принудительно инициализирует базу данных"""
    db_path = "fsr.db"
    
    print("🔧 Принудительная инициализация базы данных...")
    
    # Удаляем старую базу если она существует
    if os.path.exists(db_path):
        print(f"🗑️ Удаляем старую базу данных: {db_path}")
        os.remove(db_path)
    
    try:
        # Импортируем Database
        from database import Database
        
        # Создаем новую базу данных
        print("📁 Создаем новую базу данных...")
        db = Database(db_path)
        
        print("✅ База данных успешно инициализирована!")
        print("📊 Созданы все необходимые таблицы:")
        print("   - users")
        print("   - user_activity") 
        print("   - photo_uploads")
        print("   - referral_invites")
        print("   - giveaway_prizes")
        print("   - giveaway_participants")
        print("   - giveaway_channels")
        print("   - tickets_subscription")
        print("   - tickets_referral")
        print("   - Добавлены начальные призы в гивевей")
        
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при инициализации базы данных: {e}")
        return False

if __name__ == "__main__":
    force_init_database() 