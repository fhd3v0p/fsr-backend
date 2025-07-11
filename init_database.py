#!/usr/bin/env python3
"""
Скрипт для инициализации базы данных
"""

from database import Database

def main():
    print("🔧 Инициализация базы данных...")
    
    try:
        # Создаем экземпляр базы данных - это автоматически инициализирует все таблицы
        db = Database()
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
        
    except Exception as e:
        print(f"❌ Ошибка при инициализации базы данных: {e}")
        return False
    
    return True

if __name__ == "__main__":
    main() 