#!/usr/bin/env python3
import asyncio
import os
import sys
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Добавляем текущую директорию в путь для импорта
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import ReportDatabase, ReportBot

async def send_yesterday_report():
    """Отправка отчета за вчера"""
    load_dotenv()

    # Проверяем переменные окружения
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('GROUP_CHAT_ID')

    if not token or not chat_id:
        print("Ошибка: Не найдены TELEGRAM_BOT_TOKEN или GROUP_CHAT_ID в .env")
        return False

    try:
        # Создаем бота и отправляем отчет
        bot = ReportBot()
        await bot.send_daily_report()
        return True
    except Exception as e:
        print(f"Ошибка при отправке отчета: {e}")
        return False

if __name__ == "__main__":
    success = asyncio.run(send_yesterday_report())
    if success:
        print("Отчет за вчера отправлен успешно!")
    else:
        print("Не удалось отправить отчет.")
