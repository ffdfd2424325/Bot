import sqlite3
import os
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()
DATABASE_PATH = os.getenv('DATABASE_PATH', 'reports.db')

def check_server_db():
    """Проверка базы данных на сервере"""
    try:
        with sqlite3.connect(DATABASE_PATH) as conn:
            cursor = conn.execute('SELECT COUNT(*) FROM reports')
            count = cursor.fetchone()[0]
            print(f"Количество записей в базе данных: {count}")

            # Вывести последние записи
            cursor = conn.execute('SELECT id, user_tag, report_type, day_number, datetime, username FROM reports ORDER BY datetime DESC LIMIT 10')
            records = cursor.fetchall()
            print("\nПоследние 10 записей:")
            for record in records:
                print(f"ID: {record[0]}, {record[1]} - {record[2]}{record[3]}, дата: {record[4]}, пользователь: {record[5]}")

    except Exception as e:
        print(f"Ошибка при проверке базы данных: {e}")

if __name__ == "__main__":
    check_server_db()
