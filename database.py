"""
Модуль для работы с базой данных SQLite
"""
import sqlite3
import secrets
import string
import hashlib
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime


class Database:
    """Класс для работы с SQLite базой данных"""
    
    def __init__(self, db_file: str = "database.db"):
        """
        Инициализация базы данных
        
        Args:
            db_file: Путь к файлу базы данных SQLite
        """
        self.base_path = Path(__file__).parent
        self.db_file = self.base_path / db_file
        self._init_database()
    
    def _get_connection(self):
        """Создает и возвращает соединение с базой данных"""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row  # Для получения результатов как словарей
        return conn
    
    def _init_database(self):
        """Инициализирует базу данных и создает таблицы, если их нет"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Создаем таблицу users
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                user_type TEXT NOT NULL,
                gender TEXT,
                age INTEGER,
                interests TEXT,
                birth_date TEXT,
                start_date_bank TEXT,
                years_collaboration INTEGER,
                telegram_chat_id TEXT,
                referral_code TEXT UNIQUE
            )
        """)
        
        # Создаем таблицу holidays
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS holidays (
                id INTEGER PRIMARY KEY,
                holiday_name TEXT NOT NULL,
                date_fixed TEXT NOT NULL,
                description TEXT
            )
        """)
        
        # Создаем индексы для ускорения поиска
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_birth_date ON users(birth_date)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_chat_id ON users(telegram_chat_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_users_referral_code ON users(referral_code)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_holidays_date_fixed ON holidays(date_fixed)")
        
        conn.commit()
        conn.close()
    
    def get_users(self) -> List[Dict]:
        """
        Получает список всех пользователей
        
        Returns:
            Список словарей с данными пользователей
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users")
        rows = cursor.fetchall()
        
        conn.close()
        
        # Преобразуем Row объекты в словари
        return [dict(row) for row in rows]
    
    def get_holidays(self) -> List[Dict]:
        """
        Получает список всех праздников
        
        Returns:
            Список словарей с данными праздников
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM holidays")
        rows = cursor.fetchall()
        
        conn.close()
        
        # Преобразуем Row объекты в словари
        return [dict(row) for row in rows]
    
    def get_users_by_birthday(self, date: str) -> List[Dict]:
        """
        Получает пользователей, у которых день рождения в указанную дату
        
        Args:
            date: Дата в формате DD.MM или YYYY-MM-DD
        
        Returns:
            Список пользователей с днем рождения в эту дату
        """
        # Нормализуем формат даты
        if '.' in date:
            # Формат DD.MM.YYYY или DD.MM
            day_month = date.split('.')[:2]
            target_day = day_month[0].zfill(2)
            target_month = day_month[1].zfill(2)
        elif '-' in date:
            # Формат YYYY-MM-DD
            parts = date.split('-')
            target_day = parts[2].zfill(2)
            target_month = parts[1].zfill(2)
        else:
            return []
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Ищем пользователей по дню и месяцу рождения
        # Формат birth_date: YYYY-MM-DD
        cursor.execute("""
            SELECT * FROM users 
            WHERE birth_date IS NOT NULL 
            AND birth_date != ''
            AND SUBSTR(birth_date, 6, 2) = ?
            AND SUBSTR(birth_date, 9, 2) = ?
        """, (target_month, target_day))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_holidays_by_date(self, date: str) -> List[Dict]:
        """
        Получает праздники, которые выпадают на указанную дату
        
        Args:
            date: Дата в формате DD.MM или YYYY-MM-DD
        
        Returns:
            Список праздников на эту дату
        """
        # Нормализуем формат даты
        if '.' in date:
            # Формат DD.MM.YYYY или DD.MM
            parts = date.split('.')
            target_day = parts[0].zfill(2)
            target_month = parts[1].zfill(2)
        elif '-' in date:
            # Формат YYYY-MM-DD
            parts = date.split('-')
            target_day = parts[2].zfill(2)
            target_month = parts[1].zfill(2)
        else:
            return []
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Формат date_fixed: MM-DD (например, 01-01, 02-23)
        # Ищем праздники по дню и месяцу
        cursor.execute("""
            SELECT * FROM holidays 
            WHERE date_fixed IS NOT NULL 
            AND date_fixed != ''
            AND (
                (LENGTH(date_fixed) = 5 AND SUBSTR(date_fixed, 1, 2) = ? AND SUBSTR(date_fixed, 4, 2) = ?)
                OR
                (LENGTH(date_fixed) = 10 AND SUBSTR(date_fixed, 6, 2) = ? AND SUBSTR(date_fixed, 9, 2) = ?)
            )
        """, (target_month, target_day, target_month, target_day))
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_users_for_holiday(self, holiday: Dict, current_date: Optional[str] = None) -> List[Dict]:
        """
        Получает список пользователей, которым нужно отправить поздравление по празднику
        
        Args:
            holiday: Словарь с данными праздника
            current_date: Текущая дата (опционально, для дней рождения)
        
        Returns:
            Список пользователей для поздравления
        """
        description = holiday.get('description', '').lower()
        holiday_name = holiday.get('holiday_name', '')
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # Базовое условие: пользователь должен быть активирован (есть telegram_chat_id)
        base_condition = "telegram_chat_id IS NOT NULL AND telegram_chat_id != ''"
        
        # Определяем, кому отправлять поздравление
        if 'для всех' in description:
            query = f"SELECT * FROM users WHERE {base_condition}"
            cursor.execute(query)
        elif 'для мужчин' in description:
            query = f"SELECT * FROM users WHERE {base_condition} AND LOWER(gender) = 'male'"
            cursor.execute(query)
        elif 'для женщин' in description:
            query = f"SELECT * FROM users WHERE {base_condition} AND LOWER(gender) = 'female'"
            cursor.execute(query)
        elif 'для сотрудников' in description:
            query = f"SELECT * FROM users WHERE {base_condition} AND LOWER(user_type) = 'employee'"
            cursor.execute(query)
        elif 'для клиентов' in description:
            query = f"SELECT * FROM users WHERE {base_condition} AND LOWER(user_type) = 'client'"
            cursor.execute(query)
        elif 'it' in description.lower() or 'кибербезопасности' in holiday_name.lower():
            # Для IT-специалистов (проверяем интересы)
            query = f"""
                SELECT * FROM users 
                WHERE {base_condition}
                AND (
                    UPPER(interests) LIKE '%IT%' 
                    OR LOWER(interests) LIKE '%кибербезопасность%'
                    OR LOWER(interests) LIKE '%технологии%'
                    OR LOWER(interests) LIKE '%гаджеты%'
                )
            """
            cursor.execute(query)
        else:
            conn.close()
            return []
        
        rows = cursor.fetchall()
        conn.close()
        
        return [dict(row) for row in rows]
    
    def get_today_celebrations(self) -> Dict[str, List[Dict]]:
        """
        Получает все празднования на сегодня
        
        Returns:
            Словарь с ключами:
            - 'birthdays': список пользователей с днем рождения сегодня
            - 'holidays': список праздников сегодня
            - 'users_by_holiday': словарь {holiday_id: [users]} - пользователи для каждого праздника
        """
        today = datetime.now()
        today_str = today.strftime("%Y-%m-%d")
        today_dd_mm = today.strftime("%d.%m")
        
        result = {
            'birthdays': [],
            'holidays': [],
            'users_by_holiday': {}
        }
        
        # Получаем дни рождения
        result['birthdays'] = self.get_users_by_birthday(today_dd_mm)
        
        # Получаем праздники
        result['holidays'] = self.get_holidays_by_date(today_str)
        
        # Для каждого праздника определяем пользователей
        for holiday in result['holidays']:
            holiday_id = holiday.get('id')
            users = self.get_users_for_holiday(holiday, today_str)
            result['users_by_holiday'][holiday_id] = users
        
        return result
    
    def update_user_chat_id(self, user_id: Optional[int] = None, 
                           referral_code: Optional[str] = None,
                           chat_id: Optional[int] = None) -> bool:
        """
        Обновляет telegram_chat_id пользователя
        
        Args:
            user_id: ID пользователя
            referral_code: Реферальный код пользователя
            chat_id: Chat ID пользователя в Telegram
        
        Returns:
            True если успешно обновлено, False иначе
        """
        if not chat_id:
            return False
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            if referral_code:
                cursor.execute("""
                    UPDATE users 
                    SET telegram_chat_id = ? 
                    WHERE referral_code = ?
                """, (str(chat_id), referral_code))
            elif user_id:
                cursor.execute("""
                    UPDATE users 
                    SET telegram_chat_id = ? 
                    WHERE id = ?
                """, (str(chat_id), user_id))
            else:
                conn.close()
                return False
            
            conn.commit()
            updated = cursor.rowcount > 0
            conn.close()
            return updated
        except Exception as e:
            conn.close()
            print(f"[ERROR] Ошибка обновления chat_id: {e}")
            return False
    
    def get_user_by_referral_code(self, referral_code: str) -> Optional[Dict]:
        """
        Получает пользователя по реферальному коду
        
        Args:
            referral_code: Реферальный код
        
        Returns:
            Словарь с данными пользователя или None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE referral_code = ?", (referral_code,))
        row = cursor.fetchone()
        
        conn.close()
        
        return dict(row) if row else None
    
    def get_user_by_chat_id(self, chat_id: str) -> Optional[Dict]:
        """
        Получает пользователя по telegram_chat_id
        
        Args:
            chat_id: Chat ID пользователя в Telegram (строка)
        
        Returns:
            Словарь с данными пользователя или None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE telegram_chat_id = ?", (str(chat_id),))
        row = cursor.fetchone()
        
        conn.close()
        
        return dict(row) if row else None
    
    def generate_unique_referral_code(self, user_data: Dict, length: int = 11) -> str:
        """
        Генерирует уникальный реферальный код на основе личных данных пользователя
        
        Использует комбинацию личных данных пользователя (id, name, birth_date, start_date_bank)
        и случайной соли для создания уникального кода, который физически не может повториться.
        
        Args:
            user_data: Словарь с данными пользователя (id, name, birth_date, start_date_bank)
            length: Длина кода (по умолчанию 11)
        
        Returns:
            Уникальный реферальный код
        """
        # Алфавит для кода (без похожих символов)
        alphabet = string.ascii_letters + string.digits + '-_'
        alphabet = alphabet.replace('0', '').replace('O', '').replace('o', '')
        alphabet = alphabet.replace('I', '').replace('l', '')
        
        # Извлекаем личные данные пользователя
        user_id = str(user_data.get('id', ''))
        name = str(user_data.get('name', ''))
        birth_date = str(user_data.get('birth_date', ''))
        start_date_bank = str(user_data.get('start_date_bank', ''))
        
        # Создаем уникальную строку из личных данных
        personal_data = f"{user_id}:{name}:{birth_date}:{start_date_bank}"
        
        # Генерируем уникальный код с проверкой на уникальность
        max_attempts = 100
        for attempt in range(max_attempts):
            # Добавляем случайную соль для дополнительной уникальности
            random_salt = secrets.token_hex(16)
            
            # Создаем хеш из комбинации личных данных и соли
            combined = f"{personal_data}:{random_salt}:{attempt}"
            hash_obj = hashlib.sha256(combined.encode('utf-8'))
            hash_hex = hash_obj.hexdigest()
            
            # Преобразуем хеш в код нужной длины
            code_chars = []
            hash_index = 0
            
            for i in range(length):
                # Используем байты хеша для выбора символа из алфавита
                if hash_index >= len(hash_hex) - 1:
                    # Если хеш закончился, добавляем еще случайности
                    hash_index = 0
                    random_salt = secrets.token_hex(8)
                    hash_obj = hashlib.sha256(f"{combined}:{random_salt}".encode('utf-8'))
                    hash_hex = hash_obj.hexdigest()
                
                # Берем два символа хеша и преобразуем в индекс алфавита
                hex_pair = hash_hex[hash_index:hash_index+2]
                index = int(hex_pair, 16) % len(alphabet)
                code_chars.append(alphabet[index])
                hash_index += 2
            
            code = ''.join(code_chars)
            
            # Проверяем уникальность кода в базе данных
            if self.get_user_by_referral_code(code) is None:
                return code
        
        # Если не удалось сгенерировать уникальный код за max_attempts попыток,
        # используем полностью случайный код с timestamp
        timestamp = str(int(datetime.now().timestamp() * 1000000))[-6:]
        code = ''.join(secrets.choice(alphabet) for _ in range(length - 6)) + timestamp
        
        # Финальная проверка уникальности
        if self.get_user_by_referral_code(code) is None:
            return code
        
        # В крайнем случае добавляем еще больше случайности
        code = ''.join(secrets.choice(alphabet) for _ in range(length - 8)) + timestamp + secrets.token_hex(1)
        return code
