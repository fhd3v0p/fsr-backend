#!/bin/bash

# Упрощенный скрипт развертывания FSR API сервера
echo "🚀 Начинаем развертывание FSR API сервера..."

# Обновляем зависимости
echo "📦 Обновляем зависимости..."
pip install -r requirements.txt

# Создаем резервную копию
echo "💾 Создаем резервную копию..."
cp /etc/nginx/sites-available/default /etc/nginx/sites-available/default.backup.$(date +%Y%m%d_%H%M%S)

# Находим и заменяем секцию fsr.agency вручную
echo "⚙️ Обновляем nginx конфигурацию..."

# Создаем временный файл
cat > /tmp/nginx_update.py << 'EOF'
#!/usr/bin/env python3

with open('/etc/nginx/sites-available/default', 'r') as f:
    content = f.read()

# Находим начало и конец секции fsr.agency
start_marker = 'server_name www.fsr.agency fsr.agency; # managed by Certbot'
end_marker = '    listen [::]:443 ssl; # managed by Certbot'

# Находим позиции
start_pos = content.find(start_marker)
if start_pos == -1:
    print("Не найдена секция fsr.agency")
    exit(1)

# Ищем начало server блока
server_start = content.rfind('server {', 0, start_pos)
if server_start == -1:
    print("Не найден server блок")
    exit(1)

# Ищем конец server блока
brace_count = 0
end_pos = server_start
for i in range(server_start, len(content)):
    if content[i] == '{':
        brace_count += 1
    elif content[i] == '}':
        brace_count -= 1
        if brace_count == 0:
            end_pos = i + 1
            break

# Новая конфигурация для fsr.agency
new_config = '''    server {
        root /var/www/html;
        index index.html index.htm index.nginx-debian.html;
        server_name www.fsr.agency fsr.agency; # managed by Certbot

        # API проксирование для Flask сервера
        location /api/ {
            proxy_pass http://127.0.0.1:5000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_connect_timeout 60s;
            proxy_send_timeout 60s;
            proxy_read_timeout 60s;
            proxy_request_buffering off;
            client_max_body_size 10M;
        }

        # Health check для API
        location /health {
            proxy_pass http://127.0.0.1:5000;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }

        location / {
            try_files $uri $uri/ =404;
        }

        listen [::]:443 ssl; # managed by Certbot
        listen 443 ssl; # managed by Certbot
        ssl_certificate /etc/letsencrypt/live/fsr.agency/fullchain.pem; # managed by Certbot
        ssl_certificate_key /etc/letsencrypt/live/fsr.agency/privkey.pem; # managed by Certbot
        include /etc/letsencrypt/options-ssl-nginx.conf; # managed by Certbot
        ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem; # managed by Certbot
    }'''

# Заменяем секцию
new_content = content[:server_start] + new_config + content[end_pos:]

# Записываем обратно
with open('/etc/nginx/sites-available/default', 'w') as f:
    f.write(new_content)

print("Конфигурация nginx обновлена")
EOF

# Запускаем Python скрипт
python3 /tmp/nginx_update.py

if [ $? -eq 0 ]; then
    echo "✅ Конфигурация nginx обновлена"
    
    # Проверяем конфигурацию
    echo "🔍 Проверяем конфигурацию nginx..."
    nginx -t
    
    if [ $? -eq 0 ]; then
        echo "✅ Конфигурация nginx корректна"
        
        # Перезапускаем nginx
        echo "🔄 Перезапускаем nginx..."
        systemctl reload nginx
        
        # Копируем systemd сервис
        echo "📋 Копируем systemd сервис..."
        cp fsr-api.service /etc/systemd/system/
        
        # Перезагружаем systemd
        echo "🔄 Перезагружаем systemd..."
        systemctl daemon-reload
        
        # Останавливаем старый сервис если запущен
        echo "🛑 Останавливаем старый API сервис..."
        systemctl stop fsr-api 2>/dev/null || true
        
        # Запускаем новый сервис
        echo "🚀 Запускаем API сервис..."
        systemctl enable fsr-api
        systemctl start fsr-api
        
        # Проверяем статус
        echo "📊 Проверяем статус сервисов..."
        systemctl status fsr-api --no-pager -l
        
        echo "🎉 Развертывание завершено!"
        echo "🌐 API доступен по адресу: https://fsr.agency/api/"
        echo "💚 Health check: https://fsr.agency/health"
        
    else
        echo "❌ Ошибка в конфигурации nginx!"
        echo "Восстанавливаем резервную копию..."
        cp /etc/nginx/sites-available/default.backup.* /etc/nginx/sites-available/default
        exit 1
    fi
else
    echo "❌ Ошибка при обновлении конфигурации!"
    exit 1
fi 