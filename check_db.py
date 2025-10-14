import sqlite3

# Подключение к базе данных
conn = sqlite3.connect('reports.db')
cursor = conn.cursor()

# Получение всех записей
cursor.execute('SELECT * FROM reports ORDER BY report_date DESC, submission_time DESC')
rows = cursor.fetchall()

print("📊 Содержимое базы данных отчетов:")
print("=" * 50)

if not rows:
    print("❌ База данных пуста - отчеты еще не записывались")
else:
    print(f"✅ Найдено {len(rows)} записей:")
    print()
    for row in rows:
        id, user_tag, report_type, report_date, submission_time, username, message_id = row
        print(f"🆔 ID: {id}")
        print(f"👤 Участник: {user_tag}")
        print(f"📋 Тип отчета: {report_type}")
        print(f"📅 Дата: {report_date}")
        print(f"⏰ Время: {submission_time}")
        print(f"👥 Пользователь: {username}")
        print(f"💬 ID сообщения: {message_id}")
        print("-" * 30)

conn.close()
