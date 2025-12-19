"""
Модуль для работы с базой данных SQLite (пользователи и праздники)
"""
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
import json


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
    
    def _get_connection(self) -> sqlite3.Connection:
        """Получает соединение с базой данных"""
        conn = sqlite3.connect(self.db_file)
        conn.row_factory = sqlite3.Row  # Для доступа к колонкам по имени
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
                user_type TEXT,
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
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_birth_date ON users(birth_date)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_referral_code ON users(referral_code)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_users_telegram_chat_id ON users(telegram_chat_id)
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_holidays_date_fixed ON holidays(date_fixed)
        """)
        
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
        
        users = []
        for row in rows:
            user = dict(row)
            users.append(user)
        
        conn.close()
        return users
    
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
        
        holidays = []
        for row in rows:
            holiday = dict(row)
            holidays.append(holiday)
        
        conn.close()
        return holidays
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict]:
        """
        Получает пользователя по ID
        
        Args:
            user_id: ID пользователя
        
        Returns:
            Словарь с данными пользователя или None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
        row = cursor.fetchone()
        
        conn.close()
        return dict(row) if row else None
    
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
    
    def get_user_by_chat_id(self, chat_id: int) -> Optional[Dict]:
        """
        Получает пользователя по telegram_chat_id
        
        Args:
            chat_id: Telegram Chat ID
        
        Returns:
            Словарь с данными пользователя или None
        """
        conn = self._get_connection()
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM users WHERE telegram_chat_id = ? AND telegram_chat_id IS NOT NULL AND telegram_chat_id != ''", (str(chat_id),))
        row = cursor.fetchone()
        
        conn.close()
        return dict(row) if row else None
    
    def update_user_chat_id(self, user_id: Optional[int] = None, 
                           referral_code: Optional[str] = None, 
                           chat_id: Optional[int] = None) -> bool:
        """
        Обновляет telegram_chat_id пользователя
        
        Args:
            user_id: ID пользователя (приоритет 2)
            referral_code: Реферальный код пользователя (приоритет 1)
            chat_id: Telegram Chat ID для сохранения
        
        Returns:
            True если обновление успешно, False иначе
        """
        if not chat_id:
            return False
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Приоритет 1: поиск по реферальному коду
            if referral_code:
                cursor.execute(
                    "UPDATE users SET telegram_chat_id = ? WHERE referral_code = ?",
                    (str(chat_id), referral_code)
                )
            # Приоритет 2: поиск по user_id
            elif user_id:
                cursor.execute(
                    "UPDATE users SET telegram_chat_id = ? WHERE id = ?",
                    (str(chat_id), user_id)
                )
            else:
                conn.close()
                return False
            
            if cursor.rowcount > 0:
                conn.commit()
                conn.close()
                return True
            else:
                conn.close()
                return False
        except Exception as e:
            print(f"[ERROR] Ошибка обновления chat_id: {e}")
            conn.rollback()
            conn.close()
            return False
    
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
        
        # Ищем пользователей, у которых день рождения совпадает по дню и месяцу
        # birth_date хранится в формате YYYY-MM-DD
        cursor.execute("""
            SELECT * FROM users 
            WHERE birth_date IS NOT NULL 
            AND birth_date != ''
            AND SUBSTR(birth_date, 6, 2) = ?
            AND SUBSTR(birth_date, 9, 2) = ?
        """, (target_month, target_day))
        
        rows = cursor.fetchall()
        users = [dict(row) for row in rows]
        
        conn.close()
        return users
    
    def get_holidays_by_date(self, date: str) -> List[Dict]:
        """
        Получает праздники, которые выпадают на указанную дату
        
        Праздники сравниваются только по месяцу и дню, год не учитывается.
        
        Args:
            date: Дата в формате DD.MM, DD.MM.YYYY или YYYY-MM-DD
        
        Returns:
            Список праздников на эту дату (по месяцу и дню)
        """
        # Нормализуем формат даты - извлекаем только день и месяц
        if '.' in date:
            # Формат DD.MM.YYYY или DD.MM
            parts = date.split('.')
            target_day = parts[0].zfill(2)
            target_month = parts[1].zfill(2)
        elif '-' in date:
            # Формат YYYY-MM-DD или MM-DD
            parts = date.split('-')
            if len(parts) == 3:
                # YYYY-MM-DD
                target_day = parts[2].zfill(2)
                target_month = parts[1].zfill(2)
            elif len(parts) == 2:
                # MM-DD
                target_day = parts[1].zfill(2)
                target_month = parts[0].zfill(2)
            else:
                return []
        else:
            return []
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        # date_fixed хранится в формате MM-DD
        cursor.execute("""
            SELECT * FROM holidays 
            WHERE date_fixed = ?
        """, (f"{target_month}-{target_day}",))
        
        rows = cursor.fetchall()
        holidays = [dict(row) for row in rows]
        
        conn.close()
        return holidays
    
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
        
        # Базовое условие: пользователь должен быть активирован (иметь telegram_chat_id)
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
            # По умолчанию для всех
            query = f"SELECT * FROM users WHERE {base_condition}"
            cursor.execute(query)
        
        rows = cursor.fetchall()
        users = [dict(row) for row in rows]
        
        conn.close()
        return users
    
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
            holiday_id = holiday.get('id', '')
            users = self.get_users_for_holiday(holiday, today_str)
            result['users_by_holiday'][holiday_id] = users
        
        return result
