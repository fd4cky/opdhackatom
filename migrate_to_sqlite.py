"""
Скрипт миграции данных из CSV в SQLite
"""
import csv
import sqlite3
from pathlib import Path
from database import Database




def migrate_csv_to_sqlite():
    """Мигрирует данные из CSV файлов в SQLite базу данных"""
    base_path = Path(__file__).parent
    users_csv = base_path / "users.csv"
    holidays_csv = base_path / "holidays.csv"
    
    # Создаем экземпляр базы данных (создаст таблицы если их нет)
    db = Database()
    conn = db._get_connection()
    cursor = conn.cursor()
    
    # Очищаем существующие данные (если нужно)
    cursor.execute("DELETE FROM users")
    cursor.execute("DELETE FROM holidays")
    conn.commit()
    
    # Мигрируем пользователей
    if users_csv.exists():
        print("Миграция пользователей...")
        with open(users_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            users_count = 0
            for row in reader:
                # Генерируем уникальный код на основе данных пользователя, если его нет
                referral_code = row.get('referral_code', '').strip()
                if not referral_code:
                    referral_code = db.generate_unique_referral_code(row)
                
                cursor.execute("""
                    INSERT OR REPLACE INTO users 
                    (id, name, user_type, gender, age, interests, birth_date, 
                     start_date_bank, years_collaboration, telegram_chat_id, referral_code)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    int(row.get('id', 0)) if row.get('id') else None,
                    row.get('name', ''),
                    row.get('user_type', ''),
                    row.get('gender', ''),
                    int(row.get('age', 0)) if row.get('age') else None,
                    row.get('interests', ''),
                    row.get('birth_date', ''),
                    row.get('start_date_bank', ''),
                    int(row.get('years_collaboration', 0)) if row.get('years_collaboration') else None,
                    row.get('telegram_chat_id', '') if row.get('telegram_chat_id') else None,
                    referral_code
                ))
                users_count += 1
            print(f"✅ Мигрировано пользователей: {users_count}")
    
    # Мигрируем праздники
    if holidays_csv.exists():
        print("Миграция праздников...")
        with open(holidays_csv, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            holidays_count = 0
            for row in reader:
                cursor.execute("""
                    INSERT OR REPLACE INTO holidays 
                    (id, holiday_name, date_fixed, description)
                    VALUES (?, ?, ?, ?)
                """, (
                    int(row.get('id', 0)) if row.get('id') else None,
                    row.get('holiday_name', ''),
                    row.get('date_fixed', ''),
                    row.get('description', '')
                ))
                holidays_count += 1
            print(f"✅ Мигрировано праздников: {holidays_count}")
    
    conn.commit()
    conn.close()
    
    print("\n✅ Миграция завершена успешно!")
    print(f"База данных создана: {db.db_file}")


if __name__ == "__main__":
    migrate_csv_to_sqlite()

