import sqlite3
import os
from datetime import datetime

DATABASE_PATH = os.getenv('DATABASE_PATH', 'reports.db')

def migrate_database():
    """Миграция базы данных к новой схеме"""
    with sqlite3.connect(DATABASE_PATH) as conn:
        # Проверяем текущую схему
        cursor = conn.execute("PRAGMA table_info(reports)")
        columns = {row[1]: row for row in cursor.fetchall()}

        if 'day_number' not in columns:
            print("Выполняется миграция базы данных...")

            # Создаем временную таблицу с новой схемой
            conn.execute('''
                CREATE TABLE reports_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_tag TEXT NOT NULL,
                    report_type TEXT NOT NULL,
                    day_number INTEGER NOT NULL,
                    datetime TEXT NOT NULL,
                    username TEXT,
                    message_id INTEGER,
                    UNIQUE(user_tag, report_type, day_number)
                )
            ''')

            # Копируем данные из старой таблицы в новую (если она существует)
            try:
                cursor = conn.execute('SELECT * FROM reports')
                for row in cursor.fetchall():
                    if len(row) == 7:  # Старая схема
                        id, user_tag, report_type, report_date, submission_time, username, message_id = row
                        # Объединяем дату и время в полный datetime
                        try:
                            dt = datetime.fromisoformat(f"{report_date}T{submission_time}")
                            dt_str = dt.isoformat()
                            # По умолчанию номер дня = 1 для старых записей
                            day_number = 1
                        except ValueError:
                            dt_str = datetime.now().isoformat()
                            day_number = 1

                        conn.execute('''
                            INSERT INTO reports_new (user_tag, report_type, day_number, datetime, username, message_id)
                            VALUES (?, ?, ?, ?, ?, ?)
                        ''', (user_tag, report_type, day_number, dt_str, username, message_id))
            except sqlite3.OperationalError:
                # Таблица не существует или уже новая
                pass

            # Удаляем старую таблицу и переименовываем новую
            try:
                conn.execute('DROP TABLE reports')
            except sqlite3.OperationalError:
                pass
            conn.execute('ALTER TABLE reports_new RENAME TO reports')

            conn.commit()
            print("Миграция завершена успешно.")
        else:
            print("База данных уже использует новую схему.")

if __name__ == "__main__":
    migrate_database()
