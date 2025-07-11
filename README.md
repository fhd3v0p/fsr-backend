# FSR (Fresh Style Russia) - Telegram Bot & Web App

Полная система для Telegram бота и Flutter Web App с AI-поиском артистов.

## 🚀 Быстрый старт

### 1. Структура проекта
```
telegram_bot/
├── bot.py              # Telegram бот
├── api_server.py       # Flask API сервер
├── database.py         # Работа с БД
├── config.py           # Конфигурация
├── logger.py           # Логирование
├── health_check.py     # Проверка здоровья системы
├── system_monitor.py   # Автоматический мониторинг
├── fsr-bot.service     # Systemd сервис для бота
├── fsr-api.service     # Systemd сервис для API
└── requirements.txt    # Python зависимости
```

### 2. Установка и настройка

#### На сервере:
```bash
# Клонируем проект
cd /root
git clone <repository> telegram_bot
cd telegram_bot

# Устанавливаем зависимости
pip3 install -r requirements.txt

# Создаем .env файл
cat > .env << EOF
BOT_TOKEN=your_bot_token_here
ADMIN_CHAT_ID=your_admin_chat_id
WEBAPP_URL=https://fsr.agency
GIVEAWAY_LINK=https://t.me/addlist/f3YaeLmoNsdkYjVl
EOF

# Настраиваем systemd сервисы
cp fsr-bot.service /etc/systemd/system/
cp fsr-api.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable fsr-bot fsr-api
systemctl start fsr-bot fsr-api

# Настраиваем nginx
cp nginx_fsr_agency.conf /etc/nginx/sites-available/fsr.agency
ln -s /etc/nginx/sites-available/fsr.agency /etc/nginx/sites-enabled/
systemctl restart nginx

# Настраиваем автоматический мониторинг
chmod +x system_monitor.py
echo "*/5 * * * * /root/telegram_bot/system_monitor.py" | crontab -
```

### 3. Команды бота

- `/start` - Приветствие и основное меню
- `/giveaway` - Ссылка на розыгрыш
- `/stats` - Статистика пользователей (только для админа)
- `/help` - Справка

### 4. API Endpoints

- `GET /health` - Проверка здоровья API
- `GET /stats` - Статистика загрузок
- `POST /upload-photo` - Загрузка фото
- `GET /photos/{user_id}` - Фото пользователя

### 5. Flutter Web App

#### Основные экраны:
- **Welcome Screen** - Приветствие с анимированными аватарами
- **Giveaway Screen** - Розыгрыш с таймером
- **Role Selection** - Выбор роли (клиент/артист)
- **City Selection** - Выбор города
- **Master Cloud** - Облако мастеров по категориям
- **Master Detail** - Детальная страница мастера
- **AI Photo Search** - AI-поиск по фото
- **Master Join Info** - Информация для артистов

#### Функции:
- ✅ Загрузка фото через HTML5 File API
- ✅ Валидация файлов (только фото/видео)
- ✅ Сохранение в базу данных
- ✅ Работа в браузере и Telegram Web App
- ✅ Адаптивный дизайн
- ✅ Анимации и переходы

### 6. Мониторинг и обслуживание

#### Автоматический мониторинг:
- Проверка сервисов каждые 5 минут
- Автоматический перезапуск при сбоях
- Мониторинг памяти и диска
- Очистка логов и временных файлов

#### Ручная проверка:
```bash
# Проверка здоровья системы
python3 health_check.py

# Просмотр логов
tail -f system_monitor.log
tail -f bot.log

# Статус сервисов
systemctl status fsr-bot fsr-api nginx
```

### 7. Развертывание обновлений

#### Telegram Bot:
```bash
# Остановить сервисы
systemctl stop fsr-bot fsr-api

# Обновить код
git pull

# Перезапустить
systemctl start fsr-bot fsr-api
```

#### Flutter Web App:
```bash
# Собрать
flutter build web --release

# Развернуть
scp -r build/web/* root@server:/var/www/html/
```

### 8. Конфигурация

#### Переменные окружения (.env):
```
BOT_TOKEN=your_telegram_bot_token
ADMIN_CHAT_ID=your_admin_chat_id
WEBAPP_URL=https://fsr.agency
GIVEAWAY_LINK=https://t.me/addlist/f3YaeLmoNsdkYjVl
```

#### Nginx конфигурация:
- Проксирование `/api/` на Flask сервер
- SSL сертификаты
- Кэширование статических файлов

### 9. Безопасность

- ✅ HTTPS для всех соединений
- ✅ Валидация загружаемых файлов
- ✅ Ограничение размера файлов (10MB)
- ✅ Логирование всех действий
- ✅ Автоматическое обновление сертификатов

### 10. Производительность

#### Оптимизации:
- Кэширование статических файлов
- Сжатие ответов API
- Автоматическая очистка памяти
- Мониторинг ресурсов

#### Ограничения:
- Максимум 10MB на файл
- Поддержка только фото/видео
- Автоматический перезапуск при утечках памяти

### 11. Логирование

#### Логи:
- `bot.log` - Логи Telegram бота
- `api_server.log` - Логи API сервера
- `system_monitor.log` - Логи мониторинга
- `health_check.log` - Логи проверки здоровья

#### Отправка в Telegram:
- Все действия пользователей
- Ошибки системы
- Статистика использования

### 12. Поддержка

#### Полезные команды:
```bash
# Перезапуск всех сервисов
systemctl restart fsr-bot fsr-api nginx

# Просмотр логов в реальном времени
journalctl -u fsr-bot -f
journalctl -u fsr-api -f

# Проверка SSL сертификатов
certbot certificates

# Очистка системы
apt-get autoremove -y
journalctl --vacuum-time=7d
```

#### Контакты:
- Telegram: @FSR_Adminka
- Email: support@fsr.agency

---

**FSR (Fresh Style Russia)** - Найди умнее, соединись быстрее с AI-поиском! 🚀 