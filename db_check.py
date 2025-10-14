import sqlite3

conn = sqlite3.connect('reports.db')
cursor = conn.cursor()

# Проверяем таблицы
cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
tables = cursor.fetchall()
print('Таблицы в базе данных:', tables)

# Если таблица reports существует, считаем записи
if tables and any(table[0] == 'reports' for table in tables):
    cursor.execute('SELECT COUNT(*) FROM reports')
    count = cursor.fetchone()[0]
    print(f'Количество записей в таблице reports: {count}')

    # Показываем последние записи
    cursor.execute('SELECT * FROM reports ORDER BY id DESC LIMIT 5')
    rows = cursor.fetchall()
    if rows:
        print('\nПоследние записи:')
        for row in rows:
            print(row)
else:
    print('Таблица reports не найдена')

conn.close()
