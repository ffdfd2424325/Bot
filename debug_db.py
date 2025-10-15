#!/usr/bin/env python3
import sqlite3
import os

db_path = 'reports.db'
print(f'Путь к БД: {db_path}')
print(f'Файл существует: {os.path.exists(db_path)}')

if os.path.exists(db_path):
    with sqlite3.connect(db_path) as conn:
        # Проверим таблицу
        cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        print(f'Таблицы в БД: {[t[0] for t in tables]}')

        # Проверим содержимое
        if tables:
            cursor = conn.execute('SELECT COUNT(*) FROM reports')
            count = cursor.fetchone()[0]
            print(f'Записей в таблице reports: {count}')

            # Покажем последние записи
            cursor = conn.execute('SELECT * FROM reports ORDER BY id DESC LIMIT 3')
            rows = cursor.fetchall()
            if rows:
                print('Последние записи:')
                for row in rows:
                    print(f'  ID: {row[0]}, User: {row[1]}, Type: {row[2]}, Day: {row[3]}, DateTime: {row[4]}')
            else:
                print('Нет записей в таблице')
else:
    print('Файл базы данных не найден')
