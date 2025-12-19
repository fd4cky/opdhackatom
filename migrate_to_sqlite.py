"""
Скрипт миграции данных из CSV в SQLite
"""
import csv
import sqlite3
from pathlib import Path
from typing import List, Dict


def migrate_users(csv_file: Path, db_file: Path):
    """Мигрирует пользователей из CSV в SQLite"""
    print(f"📖 Читаю пользователей из {csv_file}...")
    
    if not csv_file.exists():
        print(f"❌ Файл {csv_file} не найден!")
        return False
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Очищаем таблицу (если нужно)
    cursor.execute("DELETE FROM users")
    
    users_count = 0
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Преобразуем пустые строки в None для числовых полей
            age = int(row['age']) if row.get('age', '').strip() else None
            years_collaboration = int(row['years_collaboration']) if row.get('years_collaboration', '').strip() else None
            
            # Обрабатываем пустые значения
            telegram_chat_id = row.get('telegram_chat_id', '').strip() or None
            referral_code = row.get('referral_code', '').strip() or None
            
            cursor.execute("""
                INSERT INTO users (
                    id, name, user_type, gender, age, interests, 
                    birth_date, start_date_bank, years_collaboration,
                    telegram_chat_id, referral_code
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                int(row['id']),
                row['name'],
                row.get('user_type', ''),
                row.get('gender', ''),
                age,
                row.get('interests', ''),
                row.get('birth_date', ''),
                row.get('start_date_bank', ''),
                years_collaboration,
                telegram_chat_id,
                referral_code
            ))
            users_count += 1
    
    conn.commit()
    conn.close()
    print(f"✅ Мигрировано {users_count} пользователей")
    return True


def migrate_holidays(csv_file: Path, db_file: Path):
    """Мигрирует праздники из CSV в SQLite"""
    print(f"📖 Читаю праздники из {csv_file}...")
    
    if not csv_file.exists():
        print(f"❌ Файл {csv_file} не найден!")
        return False
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Очищаем таблицу (если нужно)
    cursor.execute("DELETE FROM holidays")
    
    holidays_count = 0
    with open(csv_file, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            cursor.execute("""
                INSERT INTO holidays (id, holiday_name, date_fixed, description)
                VALUES (?, ?, ?, ?)
            """, (
                int(row['id']),
                row['holiday_name'],
                row['date_fixed'],
                row.get('description', '')
            ))
            holidays_count += 1
    
    conn.commit()
    conn.close()
    print(f"✅ Мигрировано {holidays_count} праздников")
    return True


def verify_migration(db_file: Path):
    """Проверяет корректность миграции"""
    print("\n🔍 Проверка миграции...")
    
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()
    
    # Проверяем пользователей
    cursor.execute("SELECT COUNT(*) FROM users")
    users_count = cursor.fetchone()[0]
    print(f"  Пользователей в БД: {users_count}")
    
    # Проверяем праздники
    cursor.execute("SELECT COUNT(*) FROM holidays")
    holidays_count = cursor.fetchone()[0]
    print(f"  Праздников в БД: {holidays_count}")
    
    # Проверяем пользователей с chat_id
    cursor.execute("SELECT COUNT(*) FROM users WHERE telegram_chat_id IS NOT NULL AND telegram_chat_id != ''")
    activated_users = cursor.fetchone()[0]
    print(f"  Активированных пользователей: {activated_users}")
    
    # Показываем несколько примеров
    print("\n  Примеры пользователей:")
    cursor.execute("SELECT id, name, telegram_chat_id, referral_code FROM users LIMIT 5")
    for row in cursor.fetchall():
        print(f"    ID {row[0]}: {row[1]} (chat_id: {row[2] or 'нет'}, код: {row[3] or 'нет'})")
    
    print("\n  Примеры праздников:")
    cursor.execute("SELECT id, holiday_name, date_fixed FROM holidays LIMIT 5")
    for row in cursor.fetchall():
        print(f"    ID {row[0]}: {row[1]} ({row[2]})")
    
    conn.close()
    print("\n✅ Проверка завершена")


def main():
    """Основная функция миграции"""
    base_path = Path(__file__).parent
    
    users_csv = base_path / "users.csv"
    holidays_csv = base_path / "holidays.csv"
    db_file = base_path / "database.db"
    
    print("🚀 Начинаю миграцию данных из CSV в SQLite...\n")
    
    # Инициализируем базу данных (создаст таблицы)
    from database import Database
    db = Database(db_file.name)
    print("✅ База данных инициализирована\n")
    
    # Мигрируем пользователей
    if not migrate_users(users_csv, db_file):
        print("❌ Ошибка миграции пользователей")
        return
    
    print()
    
    # Мигрируем праздники
    if not migrate_holidays(holidays_csv, db_file):
        print("❌ Ошибка миграции праздников")
        return
    
    # Проверяем миграцию
    verify_migration(db_file)
    
    print("\n🎉 Миграция завершена успешно!")
    print(f"📁 База данных создана: {db_file}")


if __name__ == "__main__":
    main()

