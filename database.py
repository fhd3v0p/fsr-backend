import sqlite3
import os
from datetime import datetime
from typing import Optional, List, Dict, Any

class Database:
    def __init__(self, db_path: str = "users.db"):
        self.db_path = db_path
        self.init_database()

    def init_database(self):
        """Инициализация базы данных с созданием всех таблиц"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Таблица пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                giveaway_completed BOOLEAN DEFAULT FALSE,
                tasks_completed INTEGER DEFAULT 0,
                referral_code TEXT UNIQUE,
                referred_by TEXT,
                referral_count INTEGER DEFAULT 0,
                total_referral_xp INTEGER DEFAULT 0,
                is_premium BOOLEAN DEFAULT FALSE
            )
        ''')

        # Таблица активности пользователей
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS user_activity (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                details TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')

        # Таблица загрузок фото
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS photo_uploads (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                category TEXT NOT NULL,
                file_id TEXT NOT NULL,
                file_name TEXT NOT NULL,
                file_size INTEGER NOT NULL,
                mime_type TEXT NOT NULL,
                upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                description TEXT,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')

        # Таблица реферальных приглашений
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS referral_invites (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                inviter_id INTEGER NOT NULL,
                invitee_id INTEGER,
                invitee_username TEXT,
                invitee_first_name TEXT,
                invite_code TEXT NOT NULL,
                invited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                joined_at TIMESTAMP,
                status TEXT DEFAULT 'pending', -- pending, joined, expired
                FOREIGN KEY (inviter_id) REFERENCES users (user_id),
                FOREIGN KEY (invitee_id) REFERENCES users (user_id)
            )
        ''')

        # Таблица подарков гивевея
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS giveaway_prizes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                description TEXT NOT NULL,
                value INTEGER NOT NULL, -- в рублях
                category TEXT NOT NULL, -- certificate, beauty_service, etc.
                image_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Таблица участников гивевея
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS giveaway_participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                referral_code TEXT,
                tasks_completed INTEGER DEFAULT 0,
                total_xp INTEGER DEFAULT 0,
                joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (user_id)
            )
        ''')

        # --- Новая таблица для каналов ---
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS giveaway_channels (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id INTEGER NOT NULL,
                username TEXT
            )
        ''')
        # Добавляем тестовый канал, если его нет
        cursor.execute('SELECT COUNT(*) FROM giveaway_channels WHERE channel_id = ?', (-1001973736826,))
        if cursor.fetchone()[0] == 0:
            cursor.execute('INSERT INTO giveaway_channels (channel_id, username) VALUES (?, ?)', (-1001973736826, 'F_S_R_US'))

        # Таблица подписки на все каналы
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tickets_subscription (
                user_id INTEGER PRIMARY KEY,
                is_subscribed_all BOOLEAN DEFAULT FALSE
            )
        ''')

        # Таблица билетов за рефералов
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tickets_referral (
                user_id INTEGER NOT NULL,
                referral_id INTEGER NOT NULL,
                PRIMARY KEY (user_id, referral_id)
            )
        ''')

        conn.commit()
        conn.close()

        # Добавляем начальные подарки в гивевей
        self._init_giveaway_prizes()

    def _init_giveaway_prizes(self):
        """Инициализация подарков гивевея"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Проверяем, есть ли уже подарки
        cursor.execute("SELECT COUNT(*) FROM giveaway_prizes")
        if cursor.fetchone()[0] == 0:
            prizes = [
                {
                    'name': 'Сертификат Золотое Яблоко',
                    'description': 'Сертификат на покупки в Золотом Яблоке на сумму 20,000 рублей',
                    'value': 20000,
                    'category': 'certificate',
                    'image_url': 'assets/golden_apple_certificate.png'
                },
                {
                    'name': 'Бьюти-услуги',
                    'description': 'Комплекс бьюти-услуг на сумму 100,000 рублей (маникюр, педикюр, окрашивание, стрижка, макияж)',
                    'value': 100000,
                    'category': 'beauty_service',
                    'image_url': 'assets/beauty_services.png'
                },
                {
                    'name': 'Telegram Premium (3 мес)',
                    'description': '3 Telegram Premium на 3 месяца',
                    'value': 50000,
                    'category': 'telegram_premium',
                    'image_url': 'assets/telegram_premium.png'
                }
            ]

            for prize in prizes:
                cursor.execute('''
                    INSERT INTO giveaway_prizes (name, description, value, category, image_url)
                    VALUES (?, ?, ?, ?, ?)
                ''', (prize['name'], prize['description'], prize['value'], prize['category'], prize['image_url']))

        conn.commit()
        conn.close()

    def add_user(self, user_id: int, username: str = None, first_name: str = None, last_name: str = None, referred_by: str = None) -> bool:
        """Добавление нового пользователя"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Генерируем уникальный реферальный код
            referral_code = self._generate_referral_code()

            cursor.execute('''
                INSERT OR IGNORE INTO users 
                (user_id, username, first_name, last_name, referral_code, referred_by)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, username, first_name, last_name, referral_code, referred_by))

            # Если пользователь был приглашен по реферальной ссылке
            if referred_by:
                self._process_referral(referred_by, user_id)

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error adding user: {e}")
            return False

    def _generate_referral_code(self) -> str:
        """Генерация уникального реферального кода"""
        import random
        import string
        
        while True:
            # Генерируем код формата FSR + 6 случайных символов
            code = "FSR" + ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM users WHERE referral_code = ?", (code,))
            exists = cursor.fetchone()[0] > 0
            conn.close()
            
            if not exists:
                return code

    def _process_referral(self, referral_code: str, new_user_id: int):
        """Обработка реферального приглашения"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Находим пользователя, который пригласил
            cursor.execute("SELECT user_id, first_name FROM users WHERE referral_code = ?", (referral_code,))
            result = cursor.fetchone()
            
            if result:
                inviter_id = result[0]
                inviter_name = result[1] or "Неизвестно"
                
                # Получаем имя приглашенного пользователя
                cursor.execute("SELECT first_name FROM users WHERE user_id = ?", (new_user_id,))
                invitee_result = cursor.fetchone()
                invitee_name = invitee_result[0] if invitee_result else "Неизвестно"
                
                # Обновляем статистику пригласившего
                cursor.execute('''
                    UPDATE users 
                    SET referral_count = referral_count + 1,
                        total_referral_xp = total_referral_xp + 100
                    WHERE user_id = ?
                ''', (inviter_id,))

                # Добавляем запись о приглашении
                cursor.execute('''
                    INSERT INTO referral_invites 
                    (inviter_id, invitee_id, invite_code, status, joined_at)
                    VALUES (?, ?, ?, 'joined', CURRENT_TIMESTAMP)
                ''', (inviter_id, new_user_id, referral_code))

                # Добавляем активность
                self.add_activity(inviter_id, "referral_success", f"Пригласил пользователя {new_user_id}")
                self.add_activity(new_user_id, "referred_by", f"Приглашен пользователем {inviter_id}")

                # Логируем приглашение в Telegram (асинхронно)
                try:
                    import asyncio
                    from logger import telegram_logger
                    asyncio.create_task(telegram_logger.log_friend_invitation(
                        inviter_id, inviter_name, new_user_id, invitee_name, referral_code
                    ))
                except Exception as log_error:
                    print(f"Error logging referral: {log_error}")

            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error processing referral: {e}")

    def get_user_referral_info(self, user_id: int) -> Dict[str, Any]:
        """Получение информации о рефералах пользователя"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT referral_code, referral_count, total_referral_xp,
                       (SELECT COUNT(*) FROM referral_invites WHERE inviter_id = users.user_id AND status = 'joined') as successful_invites
                FROM users WHERE user_id = ?
            ''', (user_id,))
            
            result = cursor.fetchone()
            conn.close()

            if result:
                return {
                    'referral_code': result[0],
                    'referral_count': result[1],
                    'total_referral_xp': result[2],
                    'successful_invites': result[3]
                }
            return None
        except Exception as e:
            print(f"Error getting referral info: {e}")
            return None

    def get_referral_link(self, user_id: int) -> str:
        """Получение реферальной ссылки пользователя"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT referral_code FROM users WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            conn.close()

            if result:
                return f"https://t.me/FSRUBOT?start=ref{result[0]}"
            return None
        except Exception as e:
            print(f"Error getting referral link: {e}")
            return None

    def get_user_by_referral_code(self, referral_code: str) -> Optional[Dict[str, Any]]:
        """Получение пользователя по реферальному коду"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT user_id, username, first_name, last_name, referral_code
                FROM users WHERE referral_code = ?
            """, (referral_code,))
            
            result = cursor.fetchone()
            conn.close()

            if result:
                return {
                    'user_id': result[0],
                    'username': result[1],
                    'first_name': result[2],
                    'last_name': result[3],
                    'referral_code': result[4]
                }
            return None
        except Exception as e:
            print(f"Error getting user by referral code: {e}")
            return None

    def get_giveaway_prizes(self) -> List[Dict[str, Any]]:
        """Получение списка подарков гивевея"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT name, description, value, category, image_url
                FROM giveaway_prizes
                ORDER BY value DESC
            ''')
            
            prizes = []
            for row in cursor.fetchall():
                prizes.append({
                    'name': row[0],
                    'description': row[1],
                    'value': row[2],
                    'category': row[3],
                    'image_url': row[4]
                })

            conn.close()
            return prizes
        except Exception as e:
            print(f"Error getting giveaway prizes: {e}")
            return []

    def add_activity(self, user_id: int, action: str, details: str = None):
        """Добавление записи активности пользователя"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO user_activity (user_id, action, details)
                VALUES (?, ?, ?)
            ''', (user_id, action, details))

            # Обновляем время последней активности
            cursor.execute('''
                UPDATE users SET last_activity = CURRENT_TIMESTAMP
                WHERE user_id = ?
            ''', (user_id,))

            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error adding activity: {e}")
    
    def complete_task(self, user_id: int, task_name: str, task_number: int):
        """Отметить выполнение задания пользователем"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Получаем информацию о пользователе
            cursor.execute("SELECT username, first_name FROM users WHERE user_id = ?", (user_id,))
            user_result = cursor.fetchone()
            
            if user_result:
                username = user_result[0] or "Не указан"
                first_name = user_result[1] or "Неизвестно"
                
                # Обновляем количество выполненных заданий
                cursor.execute('''
                    UPDATE users 
                    SET tasks_completed = tasks_completed + 1
                    WHERE user_id = ?
                ''', (user_id,))
                
                # Проверяем, завершил ли пользователь гивевей
                cursor.execute("SELECT tasks_completed, total_referral_xp FROM users WHERE user_id = ?", (user_id,))
                result = cursor.fetchone()
                
                if result and result[0] >= 2:  # Все задания выполнены
                    cursor.execute('''
                        UPDATE users 
                        SET giveaway_completed = 1
                        WHERE user_id = ?
                    ''', (user_id,))
                    
                    # Логируем завершение гивевея
                    try:
                        import asyncio
                        from logger import telegram_logger
                        asyncio.create_task(telegram_logger.log_giveaway_completion(
                            user_id, username, first_name, result[1] or 0
                        ))
                    except Exception as log_error:
                        print(f"Error logging giveaway completion: {log_error}")
                
                # Логируем выполнение задания
                try:
                    import asyncio
                    from logger import telegram_logger
                    asyncio.create_task(telegram_logger.log_task_completion(
                        user_id, username, first_name, task_name, task_number
                    ))
                except Exception as log_error:
                    print(f"Error logging task completion: {log_error}")
                
                # Добавляем активность
                self.add_activity(user_id, "task_completed", f"Выполнил задание: {task_name}")
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error completing task: {e}")
    
    def log_referral_stats(self, user_id: int):
        """Логировать реферальную статистику пользователя"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT username, first_name, referral_count, total_referral_xp FROM users WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            
            if result:
                username = result[0] or "Не указан"
                first_name = result[1] or "Неизвестно"
                referral_count = result[2] or 0
                total_xp = result[3] or 0
                
                # Логируем реферальную статистику
                try:
                    import asyncio
                    from logger import telegram_logger
                    asyncio.create_task(telegram_logger.log_referral_stats(
                        user_id, username, first_name, referral_count, total_xp
                    ))
                except Exception as log_error:
                    print(f"Error logging referral stats: {log_error}")
            
            conn.close()
        except Exception as e:
            print(f"Error logging referral stats: {e}")

    def log_folder_subscription(self, user_id: int):
        """Логировать подписку на папку с каналами"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT username, first_name FROM users WHERE user_id = ?", (user_id,))
            result = cursor.fetchone()
            
            if result:
                username = result[0] or "Не указан"
                first_name = result[1] or "Неизвестно"
                
                # Логируем подписку на папку
                try:
                    import asyncio
                    from logger import telegram_logger
                    asyncio.create_task(telegram_logger.log_folder_subscription(
                        user_id, username, first_name
                    ))
                except Exception as log_error:
                    print(f"Error logging folder subscription: {log_error}")
                
                # Добавляем активность
                self.add_activity(user_id, "folder_subscription", "Подписался на папку с каналами")
            
            conn.close()
        except Exception as e:
            print(f"Error logging folder subscription: {e}")

    def get_user_stats(self, user_id: int) -> Dict[str, Any]:
        """Получение статистики пользователя"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                SELECT u.user_id, u.username, u.first_name, u.last_name,
                       u.registered_at, u.last_activity, u.giveaway_completed,
                       u.tasks_completed, u.referral_count, u.total_referral_xp,
                       (SELECT COUNT(*) FROM photo_uploads WHERE user_id = u.user_id) as photos_uploaded
                FROM users u WHERE u.user_id = ?
            ''', (user_id,))
            
            result = cursor.fetchone()
            conn.close()

            if result:
                return {
                    'user_id': result[0],
                    'username': result[1],
                    'first_name': result[2],
                    'last_name': result[3],
                    'registered_at': result[4],
                    'last_activity': result[5],
                    'giveaway_completed': bool(result[6]),
                    'tasks_completed': result[7],
                    'referral_count': result[8],
                    'total_referral_xp': result[9],
                    'photos_uploaded': result[10]
                }
            return None
        except Exception as e:
            print(f"Error getting user stats: {e}")
            return None

    def get_global_stats(self) -> Dict[str, Any]:
        """Получение глобальной статистики"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM users")
            total_users = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM users WHERE giveaway_completed = 1")
            giveaway_completed = cursor.fetchone()[0]

            cursor.execute("SELECT COUNT(*) FROM photo_uploads")
            total_photos = cursor.fetchone()[0]

            cursor.execute("SELECT SUM(referral_count) FROM users")
            total_referrals = cursor.fetchone()[0] or 0

            cursor.execute("SELECT COUNT(*) FROM users WHERE last_activity > datetime('now', '-7 days')")
            active_users_7d = cursor.fetchone()[0]

            conn.close()

            return {
                'total_users': total_users,
                'giveaway_completed': giveaway_completed,
                'total_photos': total_photos,
                'total_referrals': total_referrals,
                'active_users_7d': active_users_7d
            }
        except Exception as e:
            print(f"Error getting global stats: {e}")
            return {}

    def add_photo_upload(self, photo_data: Dict[str, Any]) -> bool:
        """Добавление загрузки фото"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO photo_uploads 
                (id, user_id, category, file_id, file_name, file_size, mime_type, description)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                photo_data['id'],
                photo_data['userId'],
                photo_data['category'],
                photo_data['fileId'],
                photo_data['fileName'],
                photo_data['fileSize'],
                photo_data['mimeType'],
                photo_data.get('description')
            ))

            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error adding photo upload: {e}")
            return False

    def get_photo_stats(self) -> Dict[str, Any]:
        """Получение статистики загрузок фото"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("SELECT COUNT(*) FROM photo_uploads")
            total_uploads = cursor.fetchone()[0]

            cursor.execute('''
                SELECT category, COUNT(*) as count
                FROM photo_uploads
                GROUP BY category
            ''')
            
            category_stats = {}
            for row in cursor.fetchall():
                category_stats[row[0]] = row[1]

            cursor.execute('''
                SELECT id, user_id, category, file_name, upload_date
                FROM photo_uploads
                ORDER BY upload_date DESC
                LIMIT 10
            ''')
            
            recent_uploads = []
            for row in cursor.fetchall():
                recent_uploads.append({
                    'id': row[0],
                    'user_id': row[1],
                    'category': row[2],
                    'file_name': row[3],
                    'upload_date': row[4]
                })

            conn.close()

            return {
                'totalUploads': total_uploads,
                'categoryStats': category_stats,
                'recentUploads': len(recent_uploads)
            }
        except Exception as e:
            print(f"Error getting photo stats: {e}")
            return {'totalUploads': 0, 'categoryStats': {}, 'recentUploads': 0} 

    def add_ticket_for_referral_start(self, inviter_id: int, invitee_id: int) -> bool:
        """Начисляет 1 билет пригласившему, если друг стартует по реф-ссылке (только 1 раз за invitee)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            # Проверяем, не начислен ли уже билет за этого invitee
            cursor.execute('''
                SELECT COUNT(*) FROM referral_invites WHERE inviter_id = ? AND invitee_id = ?
            ''', (inviter_id, invitee_id))
            if cursor.fetchone()[0] > 0:
                conn.close()
                return False  # Уже начислен
            # Добавляем запись о приглашении
            cursor.execute('''
                INSERT INTO referral_invites (inviter_id, invitee_id, invite_code, status, joined_at)
                VALUES (?, ?, '', 'joined', CURRENT_TIMESTAMP)
            ''', (inviter_id, invitee_id))
            # Увеличиваем счетчик билетов (referral_count)
            cursor.execute('''
                UPDATE users SET referral_count = referral_count + 1 WHERE user_id = ?
            ''', (inviter_id,))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Error adding ticket for referral start: {e}")
            return False

    def set_subscription_status(self, user_id: int, is_subscribed_all: bool):
        """Устанавливает статус подписки на все каналы (True/False)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM tickets_subscription WHERE user_id = ?', (user_id,))
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                'INSERT INTO tickets_subscription (user_id, is_subscribed_all) VALUES (?, ?)',
                (user_id, is_subscribed_all)
            )
        else:
            cursor.execute(
                'UPDATE tickets_subscription SET is_subscribed_all = ? WHERE user_id = ?',
                (is_subscribed_all, user_id)
            )
        conn.commit()
        conn.close()

    def add_referral_ticket(self, user_id: int, referral_id: int):
        """Добавляет билет за реферала (одна запись на каждого приглашённого)"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT COUNT(*) FROM tickets_referral WHERE user_id = ? AND referral_id = ?', (user_id, referral_id))
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                'INSERT INTO tickets_referral (user_id, referral_id) VALUES (?, ?)',
                (user_id, referral_id)
            )
            conn.commit()
        conn.close()

    def set_user_premium(self, user_id: int, is_premium: bool):
        """Устанавливает статус Telegram Premium"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('UPDATE users SET is_premium = ? WHERE user_id = ?', (is_premium, user_id))
        conn.commit()
        conn.close()

    def get_user_tickets(self, user_id: int) -> int:
        """Возвращает количество билетов пользователя (1 за подписку на все каналы + 1 за каждого реферала)"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            # Билет за подписку
            cursor.execute('SELECT is_subscribed_all FROM tickets_subscription WHERE user_id = ?', (user_id,))
            sub = cursor.fetchone()
            tickets_sub = 1 if sub and sub[0] else 0
            # Билеты за рефералов
            cursor.execute('SELECT COUNT(*) FROM tickets_referral WHERE user_id = ?', (user_id,))
            tickets_ref = cursor.fetchone()[0]
            conn.close()
            return tickets_sub + tickets_ref
        except Exception as e:
            print(f"Error getting user tickets: {e}")
            return 0

    def get_task_statuses(self, user_id: int) -> dict:
        """
        Возвращает статусы выполнения заданий:
        - task1_done: подписка на папку (есть в giveaway_participants)
        - task2_done: есть хотя бы один успешный invite (referral_invites.status = 'joined')
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            # task1: подписка на папку (есть запись в giveaway_participants)
            cursor.execute('SELECT COUNT(*) FROM giveaway_participants WHERE user_id = ?', (user_id,))
            task1_done = cursor.fetchone()[0] > 0
            # task2: хотя бы один успешный invite
            cursor.execute('SELECT COUNT(*) FROM referral_invites WHERE inviter_id = ? AND status = "joined"', (user_id,))
            task2_done = cursor.fetchone()[0] > 0
            conn.close()
            return {'task1_done': task1_done, 'task2_done': task2_done}
        except Exception as e:
            print(f"Error getting task statuses: {e}")
            return {'task1_done': False, 'task2_done': False} 