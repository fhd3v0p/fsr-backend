#!/usr/bin/env python3
"""
Автоматический мониторинг и обслуживание FSR системы
Запускается по cron каждые 5 минут
"""

import os
import sys
import time
import subprocess
import logging
from datetime import datetime, timedelta
import sqlite3
import requests

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/telegram_bot/system_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FSRSystemMonitor:
    def __init__(self):
        self.base_dir = '/root/telegram_bot'
        self.db_path = os.path.join(self.base_dir, 'users.db')
        self.api_url = 'https://fsr.agency'
        self.services = ['fsr-api', 'fsr-bot', 'nginx']
        self.last_restart_file = os.path.join(self.base_dir, 'last_restart.txt')
        
    def check_service_status(self, service_name):
        """Проверка статуса сервиса"""
        try:
            result = subprocess.run(
                ['systemctl', 'is-active', service_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0 and result.stdout.strip() == 'active'
        except Exception as e:
            logger.error(f"Ошибка проверки сервиса {service_name}: {e}")
            return False
    
    def restart_service(self, service_name):
        """Перезапуск сервиса"""
        try:
            logger.info(f"Перезапуск сервиса {service_name}...")
            subprocess.run(['systemctl', 'restart', service_name], check=True)
            time.sleep(5)  # Ждем запуска
            
            # Проверяем, что сервис запустился
            if self.check_service_status(service_name):
                logger.info(f"✅ Сервис {service_name} успешно перезапущен")
                return True
            else:
                logger.error(f"❌ Сервис {service_name} не запустился после перезапуска")
                return False
        except Exception as e:
            logger.error(f"Ошибка перезапуска сервиса {service_name}: {e}")
            return False
    
    def check_api_health(self):
        """Проверка здоровья API"""
        try:
            response = requests.get(f"{self.api_url}/health", timeout=10)
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Ошибка проверки API: {e}")
            return False
    
    def check_memory_usage(self):
        """Проверка использования памяти"""
        try:
            with open('/proc/meminfo', 'r') as f:
                lines = f.readlines()
                
            mem_info = {}
            for line in lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    mem_info[key.strip()] = int(value.split()[0])
            
            total_mb = mem_info.get('MemTotal', 0) // 1024
            available_mb = mem_info.get('MemAvailable', 0) // 1024
            used_mb = total_mb - available_mb
            usage_percent = (used_mb / total_mb) * 100 if total_mb > 0 else 0
            
            logger.info(f"💾 Память: {used_mb}MB/{total_mb}MB ({usage_percent:.1f}%)")
            
            # Если память > 90%, запускаем сборщик мусора
            if usage_percent > 90:
                logger.warning("⚠️ Высокое использование памяти! Запускаем сборщик мусора...")
                self.cleanup_memory()
                
            return usage_percent
        except Exception as e:
            logger.error(f"Ошибка проверки памяти: {e}")
            return 0
    
    def cleanup_memory(self):
        """Очистка памяти"""
        try:
            # Перезапускаем API сервер для освобождения памяти
            if self.restart_service('fsr-api'):
                logger.info("✅ API сервер перезапущен для очистки памяти")
            
            # Очищаем логи если они слишком большие
            log_files = [
                '/root/telegram_bot/health_check.log',
                '/root/telegram_bot/system_monitor.log',
                '/root/telegram_bot/bot.log'
            ]
            
            for log_file in log_files:
                if os.path.exists(log_file):
                    size_mb = os.path.getsize(log_file) / (1024 * 1024)
                    if size_mb > 10:  # Если лог больше 10MB
                        logger.info(f"Очистка лога {log_file} (размер: {size_mb:.1f}MB)")
                        with open(log_file, 'w') as f:
                            f.write(f"# Лог очищен {datetime.now()}\n")
                            
        except Exception as e:
            logger.error(f"Ошибка очистки памяти: {e}")
    
    def check_database_integrity(self):
        """Проверка целостности базы данных"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Проверяем таблицы
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            
            required_tables = ['users', 'photo_uploads']
            for table in required_tables:
                if table not in tables:
                    logger.error(f"❌ Отсутствует таблица {table}")
                    return False
            
            # Проверяем количество записей
            cursor.execute("SELECT COUNT(*) FROM users;")
            user_count = cursor.fetchone()[0]
            
            cursor.execute("SELECT COUNT(*) FROM photo_uploads;")
            photo_count = cursor.fetchone()[0]
            
            logger.info(f"🗄️ БД: {user_count} пользователей, {photo_count} фото")
            
            conn.close()
            return True
            
        except Exception as e:
            logger.error(f"Ошибка проверки БД: {e}")
            return False
    
    def check_disk_space(self):
        """Проверка свободного места на диске"""
        try:
            result = subprocess.run(
                ['df', '-h', '/'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if len(lines) > 1:
                    parts = lines[1].split()
                    if len(parts) >= 5:
                        usage = parts[4]
                        usage_percent = int(usage.rstrip('%'))
                        
                        logger.info(f"💿 Диск: {usage} использовано")
                        
                        if usage_percent > 90:
                            logger.warning("⚠️ Мало места на диске!")
                            self.cleanup_disk()
                            
                        return usage_percent
                        
        except Exception as e:
            logger.error(f"Ошибка проверки диска: {e}")
            return 0
    
    def cleanup_disk(self):
        """Очистка диска"""
        try:
            # Очищаем временные файлы
            subprocess.run(['apt-get', 'autoclean'], check=True)
            subprocess.run(['apt-get', 'autoremove', '-y'], check=True)
            
            # Очищаем логи
            subprocess.run(['journalctl', '--vacuum-time=7d'], check=True)
            
            logger.info("✅ Очистка диска завершена")
            
        except Exception as e:
            logger.error(f"Ошибка очистки диска: {e}")
    
    def check_last_restart(self):
        """Проверяем, когда последний раз перезапускали сервисы"""
        try:
            if os.path.exists(self.last_restart_file):
                with open(self.last_restart_file, 'r') as f:
                    last_restart = datetime.fromisoformat(f.read().strip())
                
                # Если прошло больше часа, можно перезапускать
                if datetime.now() - last_restart > timedelta(hours=1):
                    return True
                else:
                    return False
            else:
                return True
        except Exception:
            return True
    
    def update_last_restart(self):
        """Обновляем время последнего перезапуска"""
        try:
            with open(self.last_restart_file, 'w') as f:
                f.write(datetime.now().isoformat())
        except Exception as e:
            logger.error(f"Ошибка обновления времени перезапуска: {e}")
    
    def run_monitoring(self):
        """Запуск мониторинга"""
        logger.info("🔍 Запуск мониторинга FSR системы...")
        
        issues_found = []
        
        # Проверяем сервисы
        for service in self.services:
            if not self.check_service_status(service):
                logger.error(f"❌ Сервис {service} неактивен")
                issues_found.append(f"Сервис {service} неактивен")
                
                # Перезапускаем если прошло достаточно времени
                if self.check_last_restart():
                    if self.restart_service(service):
                        self.update_last_restart()
                    else:
                        logger.error(f"❌ Не удалось перезапустить {service}")
        
        # Проверяем API
        if not self.check_api_health():
            logger.error("❌ API недоступен")
            issues_found.append("API недоступен")
        
        # Проверяем БД
        if not self.check_database_integrity():
            logger.error("❌ Проблемы с базой данных")
            issues_found.append("Проблемы с БД")
        
        # Проверяем ресурсы
        memory_usage = self.check_memory_usage()
        disk_usage = self.check_disk_space()
        
        if memory_usage and memory_usage > 90:
            issues_found.append("Высокое использование памяти")
        
        if disk_usage and disk_usage > 90:
            issues_found.append("Мало места на диске")
        
        # Логируем результаты
        if issues_found:
            logger.warning(f"⚠️ Найдено {len(issues_found)} проблем: {', '.join(issues_found)}")
        else:
            logger.info("✅ Все системы работают корректно")
        
        return len(issues_found) == 0

def main():
    monitor = FSRSystemMonitor()
    success = monitor.run_monitoring()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main() 