#!/bin/bash

echo "🔄 Полный сброс FSR Backend..."
echo "================================"

# Переходим в директорию backend
cd /opt/fsr-backend

# Останавливаем сервисы
echo "⏹️ Останавливаем сервисы..."
sudo systemctl stop fsr-api.service
sudo systemctl stop fsr-bot.service

# Сбрасываем базу данных
echo "🗑️ Сбрасываем базу данных..."
python3 reset_db.py

# Перезапускаем сервисы
echo "🚀 Перезапускаем сервисы..."
sudo systemctl start fsr-bot.service
sudo systemctl start fsr-api.service

# Проверяем статус
echo "📊 Проверяем статус сервисов..."
echo "--- API сервис ---"
sudo systemctl status fsr-api.service --no-pager -l
echo ""
echo "--- Bot сервис ---"
sudo systemctl status fsr-bot.service --no-pager -l

# Проверяем API
echo ""
echo "🧪 Проверяем API..."
echo "Health check:"
curl -s https://fsr.agency/health
echo ""
echo ""
echo "Total tickets:"
curl -s https://fsr.agency/api/tickets/total
echo ""

echo "🎉 Сброс и перезапуск завершены!"
echo "🌐 API доступен по адресу: https://fsr.agency/api/"
echo "💚 Health check: https://fsr.agency/health"
echo "🎫 Total tickets: https://fsr.agency/api/tickets/total" 