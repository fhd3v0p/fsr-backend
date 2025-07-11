#!/usr/bin/env python3
"""
Скрипт для применения миграций базы данных
"""

import sqlite3
import os
import sys
from pathlib import Path

def apply_migration(db_path, migration_file):
    """Применяет миграцию из файла"""
    print(f"Применяем миграцию: {migration_file}")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Читаем SQL из файла миграции
        with open(migration_file, 'r', encoding='utf-8') as f:
            sql_content = f.read()
        
        # Выполняем SQL команды
        cursor.executescript(sql_content)
        conn.commit()
        conn.close()
        
        print(f"✅ Миграция {migration_file} успешно применена")
        return True
        
    except Exception as e:
        print(f"❌ Ошибка при применении миграции {migration_file}: {e}")
        return False

def main():
    # Путь к базе данных
    db_path = "fsr.db"
    
    if not os.path.exists(db_path):
        print(f"❌ База данных {db_path} не найдена")
        sys.exit(1)
    
    # Папка с миграциями
    migrations_dir = Path("migrations")
    
    if not migrations_dir.exists():
        print("❌ Папка migrations не найдена")
        sys.exit(1)
    
    # Получаем список файлов миграций
    migration_files = sorted([f for f in migrations_dir.glob("*.sql")])
    
    if not migration_files:
        print("ℹ️ Файлы миграций не найдены")
        return
    
    print(f"Найдено {len(migration_files)} файлов миграций:")
    for f in migration_files:
        print(f"  - {f.name}")
    
    print("\nНачинаем применение миграций...")
    
    success_count = 0
    for migration_file in migration_files:
        if apply_migration(db_path, migration_file):
            success_count += 1
    
    print(f"\n📊 Результат: {success_count}/{len(migration_files)} миграций применено успешно")
    
    if success_count == len(migration_files):
        print("✅ Все миграции применены успешно!")
    else:
        print("⚠️ Некоторые миграции не были применены")
        sys.exit(1)

if __name__ == "__main__":
    main()
