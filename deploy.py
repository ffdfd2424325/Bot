#!/usr/bin/env python3
import subprocess
import time
import os
import requests
from dotenv import load_dotenv

# Загрузка переменных окружения
load_dotenv()

# Функция для запуска команд
def run_command(cmd, cwd=None):
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

# Шаги автоматизации
def automate_deploy():
    print("Шаг 1: Деплой проекта в Railway...")
    success, out, err = run_command("railway up", cwd="e:\\Bot")
    if not success:
        print(f"Ошибка деплоя: {err}")
        return False
    print("Деплой запущен. Ждём 2 минуты...")
    time.sleep(120)  # Ждём сборки

    print("Шаг 2: Проверка логов...")
    success, logs, err = run_command("railway logs", cwd="e:\\Bot")
    if success and "main.py" in logs:
        print("Бот запущен успешно!")
        return True
    else:
        print(f"Ошибка в логах: {err}")
        return False

# Тест бота (если токен доступен)
def test_bot():
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("Токен не найден в .env")
        return
    chat_id = os.getenv("GROUP_CHAT_ID")
    if not chat_id:
        print("Chat ID не найден")
        return

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    data = {"chat_id": chat_id, "text": "Тест: Бот работает!"}
    response = requests.post(url, data=data)
    if response.status_code == 200:
        print("Тестовое сообщение отправлено успешно!")
    else:
        print(f"Ошибка отправки: {response.text}")

if __name__ == "__main__":
    if automate_deploy():
        test_bot()
    else:
        print("Деплой провалился. Проверьте настройки.")
