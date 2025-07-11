#!/bin/bash

# FSR Deployment Script
# Быстрое развертывание обновлений на сервере

set -e

echo "🚀 FSR Deployment Script"
echo "=========================="

# Проверяем аргументы
if [ "$1" = "bot" ]; then
    echo "📦 Развертывание Telegram Bot..."
    
    # Останавливаем сервисы
    echo "⏹️ Останавливаем сервисы..."
    systemctl stop fsr-bot fsr-api
    
    # Обновляем код (если используется git)
    if [ -d ".git" ]; then
        echo "📥 Обновляем код из git..."
        git pull
    fi
    
    # Устанавливаем зависимости
    echo "📦 Обновляем зависимости..."
    pip3 install -r requirements.txt
    
    # Перезапускаем сервисы
    echo "▶️ Запускаем сервисы..."
    systemctl start fsr-bot fsr-api
    
    # Проверяем статус
    echo "🔍 Проверяем статус..."
    sleep 5
    systemctl status fsr-bot fsr-api --no-pager -l
    
    echo "✅ Telegram Bot развернут!"

elif [ "$1" = "web" ]; then
    echo "🌐 Развертывание Flutter Web App..."
    
    # Проверяем, что Flutter установлен
    if ! command -v flutter &> /dev/null; then
        echo "❌ Flutter не установлен. Установите Flutter и повторите."
        exit 1
    fi
    
    # Собираем приложение
    echo "🔨 Собираем Flutter Web App..."
    flutter build web --release
    
    # Копируем на сервер
    echo "📤 Копируем на сервер..."
    scp -r build/web/* root@46.203.233.218:/var/www/html/
    
    echo "✅ Flutter Web App развернут!"

elif [ "$1" = "full" ]; then
    echo "🔄 Полное развертывание системы..."
    
    # Развертываем бота
    $0 bot
    
    # Развертываем веб-приложение
    $0 web
    
    # Проверяем здоровье системы
    echo "🏥 Проверяем здоровье системы..."
    ssh root@46.203.233.218 "cd /root/telegram_bot && python3 health_check.py"
    
    echo "✅ Полное развертывание завершено!"

elif [ "$1" = "monitor" ]; then
    echo "📊 Запуск мониторинга..."
    ssh root@46.203.233.218 "cd /root/telegram_bot && python3 system_monitor.py"

elif [ "$1" = "logs" ]; then
    echo "📋 Просмотр логов..."
    ssh root@46.203.233.218 "tail -f /root/telegram_bot/system_monitor.log"

elif [ "$1" = "status" ]; then
    echo "📊 Статус сервисов..."
    ssh root@46.203.233.218 "systemctl status fsr-bot fsr-api nginx --no-pager -l"

elif [ "$1" = "restart" ]; then
    echo "🔄 Перезапуск всех сервисов..."
    ssh root@46.203.233.218 "systemctl restart fsr-bot fsr-api nginx"
    echo "✅ Сервисы перезапущены!"

else
    echo "❌ Неизвестная команда: $1"
    echo ""
    echo "📖 Использование:"
    echo "  $0 bot     - Развернуть только Telegram Bot"
    echo "  $0 web     - Развернуть только Flutter Web App"
    echo "  $0 full    - Полное развертывание системы"
    echo "  $0 monitor - Запустить мониторинг"
    echo "  $0 logs    - Просмотр логов"
    echo "  $0 status  - Статус сервисов"
    echo "  $0 restart - Перезапуск всех сервисов"
    echo ""
    echo "💡 Примеры:"
    echo "  $0 bot     # Обновить только бота"
    echo "  $0 full    # Обновить всю систему"
    echo "  $0 status  # Проверить статус"
fi 