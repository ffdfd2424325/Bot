#!/usr/bin/env python3
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def test_telegram_connection():
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    chat_id = os.getenv('GROUP_CHAT_ID')

    if not token:
        print("❌ TELEGRAM_BOT_TOKEN не найден в .env файле")
        return False

    if not chat_id:
        print("❌ GROUP_CHAT_ID не найден в .env файле")
        return False

    try:
        # Тестируем токен
        response = requests.get(f"https://api.telegram.org/bot{token}/getMe")
        if response.status_code == 200:
            bot_info = response.json()
            print(f"✅ Бот подключен: @{bot_info['result']['username']}")
        else:
            print(f"❌ Ошибка подключения к боту: {response.text}")
            return False

        # Тестируем отправку сообщения
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = {"chat_id": chat_id, "text": "🧪 Тест соединения - бот работает!"}
        response = requests.post(url, data=data)

        if response.status_code == 200:
            print("✅ Тестовое сообщение отправлено успешно!")
            return True
        else:
            print(f"❌ Ошибка отправки сообщения: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Ошибка подключения: {e}")
        return False

if __name__ == "__main__":
    success = test_telegram_connection()
    if success:
        print("\n🎉 Все настройки корректны!")
    else:
        print("\n⚠️ Проверьте настройки в .env файле")
