#!/bin/bash

echo "🚀 Обновление FSR Backend..."
echo "=============================="

# Переходим в директорию backend
cd /opt/fsr-backend

# Получаем последние изменения из git
echo "📥 Получаем изменения из git..."
git pull origin main

if [ $? -eq 0 ]; then
    echo "✅ Код обновлен"
    
    # Перезапускаем API сервис
    echo "🔄 Перезапускаем API сервис..."
    sudo systemctl restart fsr-api.service
    
    # Проверяем статус
    echo "📊 Проверяем статус сервиса..."
    sudo systemctl status fsr-api.service --no-pager -l
    
    echo "🎉 Обновление завершено!"
    echo "🌐 API доступен по адресу: https://fsr.agency/api/"
    echo "💚 Health check: https://fsr.agency/health"
    echo "🎫 Новый эндпоинт: https://fsr.agency/api/tickets/total"
    
else
    echo "❌ Ошибка при получении изменений из git!"
    exit 1
fi 