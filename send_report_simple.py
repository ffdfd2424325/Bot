#!/usr/bin/env python3
import os
import requests
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

# Импортируем функции из main.py
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import ReportDatabase

def send_yesterday_report_simple():
    """Простая отправка отчета за вчера без полного бота"""
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('GROUP_CHAT_ID')

    if not token or not chat_id:
        print("❌ Не найдены TELEGRAM_BOT_TOKEN или GROUP_CHAT_ID")
        return False

    try:
        # Создаем базу данных
        db = ReportDatabase('reports.db')

        # Получаем вчерашнюю дату
        yesterday = datetime.now() - timedelta(days=1)
        reports = db.get_reports_for_date(yesterday)

        if not reports:
            print("❌ Нет отчетов за вчера")
            return False

        # Форматируем сообщение (используем код из main.py)
        from main import PARTICIPANTS, REPORT_TYPES

        date_str = yesterday.strftime("%d.%m.%Y")
        message_parts = [f"📊 **Сводка отчетов за {date_str}**\n"]

        all_users = list(PARTICIPANTS.values())
        tag_to_username = {v: k for k, v in PARTICIPANTS.items()}

        for report_type, info in REPORT_TYPES.items():
            submitted_users = []
            late_users = []
            missing_users = []

            if report_type == 'оу':
                deadline = datetime.combine(yesterday.date(), info['deadline'])
            else:
                deadline = datetime.combine(yesterday.date(), info['deadline'])

            for user_tag in all_users:
                if user_tag in reports and report_type in reports[user_tag]:
                    submission_time = datetime.fromisoformat(reports[user_tag][report_type]['datetime'])
                    day_number = reports[user_tag][report_type]['day_number']

                    if report_type == 'оу' and submission_time.time() > info['deadline']:
                        late_users.append(f"{tag_to_username.get(user_tag, user_tag)}({day_number})")
                    else:
                        submitted_users.append(f"{tag_to_username.get(user_tag, user_tag)}({day_number})")
                else:
                    if report_type == 'оу':
                        if datetime.now().time() > info['deadline']:
                            missing_users.append(tag_to_username.get(user_tag, user_tag))
                    else:
                        if datetime.now().date() > yesterday.date():
                            missing_users.append(tag_to_username.get(user_tag, user_tag))

            emoji = {'ос': '🏃', 'оу': '🌅', 'ов': '🌙', 'гсд': '⭐'}[report_type]
            message_parts.append(f"\n{emoji} **{info['name']}:**")

            if submitted_users:
                message_parts.append(f"✅ Вовремя: {', '.join(submitted_users)}")

            if late_users:
                message_parts.append(f"⚠️ Опоздали: {', '.join(late_users)}")

            if missing_users:
                message_parts.append(f"❌ Не сдали: {', '.join(missing_users)}")

        report_message = "\n".join(message_parts)

        # Отправляем сообщение
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = {"chat_id": chat_id, "text": report_message, "parse_mode": "Markdown"}

        response = requests.post(url, data=data)

        if response.status_code == 200:
            print("✅ Отчет за вчера отправлен успешно!")
            return True
        else:
            print(f"❌ Ошибка отправки: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

if __name__ == "__main__":
    success = send_yesterday_report_simple()
    if success:
        print("🎉 Отчет отправлен!")
    else:
        print("⚠️ Не удалось отправить отчет.")
