#!/usr/bin/env python3
"""
Скрипт проверки целостности FSR системы
Проверяет все компоненты: API сервер, базу данных, nginx, бота
"""

import os
import sys
import sqlite3
import requests
import subprocess
import json
from datetime import datetime
import logging

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/root/telegram_bot/health_check.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FSRHealthChecker:
    def __init__(self):
        self.base_dir = '/root/telegram_bot'
        self.db_path = os.path.join(self.base_dir, 'users.db')
        self.api_url = 'https://fsr.agency'
        self.results = {}
        
    def check_system_services(self):
        """Проверка системных сервисов"""
        logger.info("🔍 Проверка системных сервисов...")
        
        services = {
            'fsr-api': 'FSR API Server',
            'nginx': 'Nginx Web Server',
            'fsr-bot': 'FSR Telegram Bot'
        }
        
        for service, name in services.items():
            try:
                result = subprocess.run(
                    ['systemctl', 'is-active', service],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode == 0 and result.stdout.strip() == 'active':
                    self.results[f'{service}_status'] = '✅ Активен'
                    logger.info(f"✅ {name}: Активен")
                else:
                    self.results[f'{service}_status'] = '❌ Неактивен'
                    logger.error(f"❌ {name}: Неактивен")
                    
            except Exception as e:
                self.results[f'{service}_status'] = f'❌ Ошибка: {str(e)}'
                logger.error(f"❌ {name}: Ошибка проверки - {e}")
    
    def check_database_integrity(self):
        """Проверка целостности базы данных"""
        logger.info("🗄️ Проверка базы данных...")
        
        try:
            # Проверяем существование файла БД
            if not os.path.exists(self.db_path):
                self.results['database_file'] = '❌ Файл БД не найден'
                logger.error("❌ Файл базы данных не найден")
                return
            
            self.results['database_file'] = '✅ Файл БД существует'
            
            # Подключаемся к БД
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Проверяем таблицы
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = [row[0] for row in cursor.fetchall()]
            
            required_tables = ['users', 'photo_uploads']
            missing_tables = []
            
            for table in required_tables:
                if table in tables:
                    # Проверяем структуру таблицы
                    cursor.execute(f"PRAGMA table_info({table});")
                    columns = cursor.fetchall()
                    logger.info(f"✅ Таблица {table}: {len(columns)} колонок")
                else:
                    missing_tables.append(table)
                    logger.warning(f"⚠️ Таблица {table} отсутствует")
            
            if missing_tables:
                self.results['database_tables'] = f'⚠️ Отсутствуют таблицы: {", ".join(missing_tables)}'
            else:
                self.results['database_tables'] = '✅ Все таблицы существуют'
            
            # Проверяем количество записей
            cursor.execute("SELECT COUNT(*) FROM users;")
            user_count = cursor.fetchone()[0]
            self.results['user_count'] = f'👥 Пользователей: {user_count}'
            
            cursor.execute("SELECT COUNT(*) FROM photo_uploads;")
            photo_count = cursor.fetchone()[0]
            self.results['photo_count'] = f'📸 Фото: {photo_count}'
            
            conn.close()
            self.results['database_connection'] = '✅ Подключение к БД успешно'
            
        except Exception as e:
            self.results['database_connection'] = f'❌ Ошибка БД: {str(e)}'
            logger.error(f"❌ Ошибка проверки БД: {e}")
    
    def check_api_endpoints(self):
        """Проверка API endpoints"""
        logger.info("🌐 Проверка API endpoints...")
        
        endpoints = [
            ('/health', 'Health Check'),
            ('/api/stats', 'API Stats'),
        ]
        
        for endpoint, name in endpoints:
            try:
                response = requests.get(f"{self.api_url}{endpoint}", timeout=10)
                
                if response.status_code == 200:
                    self.results[f'api_{endpoint.replace("/", "_")}'] = f'✅ {name}: OK'
                    logger.info(f"✅ {name}: {response.status_code}")
                    
                    # Проверяем JSON ответ
                    try:
                        data = response.json()
                        if endpoint == '/api/stats':
                            stats = data.get('stats', {})
                            logger.info(f"📊 Статистика: {stats}")
                    except json.JSONDecodeError:
                        logger.warning(f"⚠️ {name}: Неверный JSON ответ")
                        
                else:
                    self.results[f'api_{endpoint.replace("/", "_")}'] = f'❌ {name}: {response.status_code}'
                    logger.error(f"❌ {name}: {response.status_code}")
                    
            except requests.exceptions.RequestException as e:
                self.results[f'api_{endpoint.replace("/", "_")}'] = f'❌ {name}: Ошибка подключения'
                logger.error(f"❌ {name}: Ошибка подключения - {e}")
    
    def check_nginx_config(self):
        """Проверка конфигурации nginx"""
        logger.info("⚙️ Проверка конфигурации nginx...")
        
        try:
            result = subprocess.run(
                ['nginx', '-t'],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                self.results['nginx_config'] = '✅ Конфигурация nginx корректна'
                logger.info("✅ Конфигурация nginx корректна")
            else:
                self.results['nginx_config'] = f'❌ Ошибка конфигурации nginx: {result.stderr}'
                logger.error(f"❌ Ошибка конфигурации nginx: {result.stderr}")
                
        except Exception as e:
            self.results['nginx_config'] = f'❌ Ошибка проверки nginx: {str(e)}'
            logger.error(f"❌ Ошибка проверки nginx: {e}")
    
    def check_ssl_certificates(self):
        """Проверка SSL сертификатов"""
        logger.info("🔒 Проверка SSL сертификатов...")
        
        try:
            response = requests.get(f"{self.api_url}/health", timeout=10, verify=True)
            
            if response.status_code == 200:
                self.results['ssl_certificate'] = '✅ SSL сертификат действителен'
                logger.info("✅ SSL сертификат действителен")
            else:
                self.results['ssl_certificate'] = f'❌ SSL ошибка: {response.status_code}'
                logger.error(f"❌ SSL ошибка: {response.status_code}")
                
        except requests.exceptions.SSLError as e:
            self.results['ssl_certificate'] = f'❌ SSL сертификат недействителен: {str(e)}'
            logger.error(f"❌ SSL сертификат недействителен: {e}")
        except Exception as e:
            self.results['ssl_certificate'] = f'❌ Ошибка проверки SSL: {str(e)}'
            logger.error(f"❌ Ошибка проверки SSL: {e}")
    
    def check_python_dependencies(self):
        """Проверка Python зависимостей"""
        logger.info("📦 Проверка Python зависимостей...")
        
        required_packages = [
            'flask',
            'flask-cors',
            'aiogram',
            'python-dotenv',
            'aiohttp'
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
                logger.info(f"✅ {package}: Установлен")
            except ImportError:
                missing_packages.append(package)
                logger.error(f"❌ {package}: Не установлен")
        
        if missing_packages:
            self.results['python_dependencies'] = f'❌ Отсутствуют пакеты: {", ".join(missing_packages)}'
        else:
            self.results['python_dependencies'] = '✅ Все зависимости установлены'
    
    def check_file_permissions(self):
        """Проверка прав доступа к файлам"""
        logger.info("📁 Проверка прав доступа...")
        
        critical_files = [
            self.db_path,
            os.path.join(self.base_dir, 'api_server.py'),
            os.path.join(self.base_dir, 'bot.py'),
            os.path.join(self.base_dir, 'config.py'),
            os.path.join(self.base_dir, '.env')
        ]
        
        for file_path in critical_files:
            if os.path.exists(file_path):
                if os.access(file_path, os.R_OK):
                    logger.info(f"✅ {os.path.basename(file_path)}: Чтение разрешено")
                else:
                    logger.error(f"❌ {os.path.basename(file_path)}: Нет прав на чтение")
            else:
                logger.error(f"❌ {os.path.basename(file_path)}: Файл не найден")
    
    def check_memory_usage(self):
        """Проверка использования памяти"""
        logger.info("💾 Проверка использования памяти...")
        
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
            
            self.results['memory_usage'] = f'💾 Память: {used_mb}MB/{total_mb}MB ({usage_percent:.1f}%)'
            logger.info(f"💾 Память: {used_mb}MB/{total_mb}MB ({usage_percent:.1f}%)")
            
            if usage_percent > 90:
                logger.warning("⚠️ Высокое использование памяти!")
                
        except Exception as e:
            logger.error(f"❌ Ошибка проверки памяти: {e}")
    
    def check_disk_space(self):
        """Проверка свободного места на диске"""
        logger.info("💿 Проверка свободного места...")
        
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
                        self.results['disk_usage'] = f'💿 Диск: {usage} использовано'
                        logger.info(f"💿 Диск: {usage} использовано")
                        
                        # Извлекаем процент использования
                        usage_percent = int(usage.rstrip('%'))
                        if usage_percent > 90:
                            logger.warning("⚠️ Мало места на диске!")
                            
        except Exception as e:
            logger.error(f"❌ Ошибка проверки диска: {e}")
    
    def generate_report(self):
        """Генерация отчета"""
        logger.info("📋 Генерация отчета...")
        
        report = f"""
🔍 ОТЧЕТ ПРОВЕРКИ FSR СИСТЕМЫ
📅 Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{'='*50}

📊 РЕЗУЛЬТАТЫ ПРОВЕРКИ:
"""
        
        for key, value in self.results.items():
            report += f"{value}\n"
        
        report += f"""
{'='*50}

💡 РЕКОМЕНДАЦИИ:
"""
        
        # Анализируем результаты и даем рекомендации
        issues = [k for k, v in self.results.items() if '❌' in v or '⚠️' in v]
        
        if not issues:
            report += "✅ Все системы работают корректно!\n"
        else:
            report += f"⚠️ Найдено {len(issues)} проблем:\n"
            for issue in issues:
                report += f"  - {self.results[issue]}\n"
        
        # Сохраняем отчет в файл
        report_path = os.path.join(self.base_dir, 'health_report.txt')
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"📋 Отчет сохранен в: {report_path}")
        print(report)
        
        return len(issues) == 0
    
    def run_full_check(self):
        """Запуск полной проверки"""
        logger.info("🚀 Запуск полной проверки FSR системы...")
        
        try:
            self.check_system_services()
            self.check_database_integrity()
            self.check_api_endpoints()
            self.check_nginx_config()
            self.check_ssl_certificates()
            self.check_python_dependencies()
            self.check_file_permissions()
            self.check_memory_usage()
            self.check_disk_space()
            
            is_healthy = self.generate_report()
            
            if is_healthy:
                logger.info("🎉 Система полностью здорова!")
                return 0
            else:
                logger.warning("⚠️ Обнаружены проблемы в системе!")
                return 1
                
        except Exception as e:
            logger.error(f"❌ Критическая ошибка при проверке: {e}")
            return 2

def main():
    checker = FSRHealthChecker()
    exit_code = checker.run_full_check()
    sys.exit(exit_code)

if __name__ == "__main__":
    main() 