#!/usr/bin/env python3
import sqlite3
import os
from datetime import datetime, timedelta
from dotenv import load_dotenv

load_dotenv()

def check_database():
    """Проверка содержимого базы данных"""
    db_path = os.getenv('DATABASE_PATH', 'reports.db')

    if not os.path.exists(db_path):
        print("❌ База данных не найдена!")
        return

    with sqlite3.connect(db_path) as conn:
        # Общая статистика
        cursor = conn.execute('SELECT COUNT(*) FROM reports')
        total_reports = cursor.fetchone()[0]

        cursor = conn.execute('SELECT COUNT(DISTINCT user_tag) FROM reports')
        unique_users = cursor.fetchone()[0]

        cursor = conn.execute('SELECT COUNT(DISTINCT date(datetime)) FROM reports')
        unique_dates = cursor.fetchone()[0]

        print("📊 Статистика базы данных:")
        print(f"   Всего отчетов: {total_reports}")
        print(f"   Уникальных участников: {unique_users}")
        print(f"   Дней с отчетами: {unique_dates}")

        # Последние 5 отчетов
        print("\n📝 Последние 5 отчетов:")
        cursor = conn.execute('''
            SELECT user_tag, report_type, datetime, username
            FROM reports
            ORDER BY datetime DESC
            LIMIT 5
        ''')

        reports = cursor.fetchall()
        if reports:
            for report in reports:
                user_tag, report_type, dt, username = report
                dt_formatted = datetime.fromisoformat(dt).strftime('%d.%m %H:%M')
                print(f"   {user_tag} → {report_type} ({dt_formatted}) @{username or 'аноним'}")
        else:
            print("   Нет отчетов в базе данных")

        # Отчеты за сегодня
        today = datetime.now().date().isoformat()
        cursor = conn.execute('SELECT COUNT(*) FROM reports WHERE date(datetime) = ?', (today,))
        today_count = cursor.fetchone()[0]

        print(f"\n📅 Отчетов за сегодня ({today}): {today_count}")

        if today_count > 0:
            cursor = conn.execute('''
                SELECT user_tag, report_type, datetime
                FROM reports
                WHERE date(datetime) = ?
                ORDER BY datetime DESC
            ''', (today,))

            today_reports = cursor.fetchall()
            for report in today_reports:
                user_tag, report_type, dt = report
                dt_formatted = datetime.fromisoformat(dt).strftime('%H:%M')
                print(f"   {user_tag} → {report_type} ({dt_formatted})")

def check_bot_logs():
    """Проверка логов бота"""
    print("\n📋 Последние логи бота:")
    print("Проверьте логи сервера для подтверждения обработки сообщений")

if __name__ == "__main__":
    print("🔍 Диагностика базы данных бота")
    print("=" * 50)
    check_database()
    check_bot_logs()
    print("\n✅ Диагностика завершена")
