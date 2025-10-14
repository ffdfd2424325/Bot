# get_ids.py
import asyncio
import logging
import os
from aiogram import Bot, Dispatcher
from aiogram.types import Message

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# ВАРИАНТ 1: Использовать переменную окружения
# BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

# ВАРИАНТ 2: Впишите токен прямо здесь (замените на ваш реальный токен)
BOT_TOKEN = "8128022865:AAFgLxyYWAUZXUtJZ1fjFhUa7GkLI-GZFcE"  # <-- ВСТАВЬТЕ СВОЙ ТОКЕН ЗДЕСЬ

# Проверка токена
if not BOT_TOKEN:
    print("❌ ОШИБКА: Токен бота не найден!")
    print("   Получите токен у @BotFather в Telegram")
    exit(1)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Флаг для остановки после получения нужного сообщения
stop_after_message = False

@dp.message()
async def handle(msg: Message):
    global stop_after_message

    if stop_after_message:
        return

    print("----- Новое сообщение получено -----")
    print("chat.id:", msg.chat.id)
    print("message_thread_id:", getattr(msg, "message_thread_id", None))
    print("from:", msg.from_user.username if msg.from_user else "Неизвестный пользователь")
    print("text:", msg.text)
    print("--------------------------------")

    # Сохраняем информацию в файл для удобства
    with open("chat_info.txt", "w", encoding="utf-8") as f:
        f.write(f"GROUP_CHAT_ID={msg.chat.id}\n")
        if hasattr(msg, "message_thread_id") and msg.message_thread_id:
            f.write(f"REPORTS_TOPIC_ID={msg.message_thread_id}\n")
        f.write(f"Сообщение от: @{msg.from_user.username if msg.from_user.username else 'unknown'}\n")
        f.write(f"Текст: {msg.text}\n")

    print("✅ Данные сохранены в файл chat_info.txt")
    print("Теперь добавьте эти значения в файл .env")

    # Корректно останавливаем бота
    stop_after_message = True
    await dp.stop_polling()
    await bot.session.close()

async def main():
    print("🚀 Запуск скрипта получения данных...")
    print("📝 Отправьте любое сообщение в тему 'Отчёты' вашей группы")
    print("⏹️  После получения сообщения бот автоматически остановится")
    print()

    try:
        await dp.start_polling(bot)
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        print("✅ Скрипт завершен")

if __name__ == "__main__":
    asyncio.run(main())
