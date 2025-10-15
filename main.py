import asyncio
import logging
import sqlite3
from datetime import datetime, time, timedelta
from typing import Dict, List, Optional, Tuple

import os
from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# Загрузка переменных окружения
load_dotenv()

# Конфигурация
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GROUP_CHAT_ID = int(os.getenv('GROUP_CHAT_ID', 0))
DATABASE_PATH = os.getenv('DATABASE_PATH', 'reports.db')
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Настройка логирования
logging.basicConfig(level=getattr(logging, LOG_LEVEL.upper()))
logger = logging.getLogger(__name__)

# Словарь участников и их тегов
PARTICIPANTS = {
    '@A_N_yaki': '#ан',
    '@Dev_Jones': '#ден',
    '@FenolIFtalein': '#никита',
    '@Igor_Lucklett': '#игорь',
    '@Melnikova_Alena': '#ал',
    '@Mikhailovmind': '#тор',
    '@Polyhakayna0': '#поли',
    '@Wlad_is_law': '#в',
    '@bleffucio': '#арк',
    '@helga_sigy': '#оля',
    '@mix_nastya': '#нася',
    '@nadezhda_efremova123': '#надя',
    '@travellove_krd': '#любовь'
}

# Типы отчетов (теперь поддерживают номера дней)
REPORT_TYPES = {
    'ос': {'name': 'Спорт', 'deadline': time(23, 59)},
    'оу': {'name': 'Утренний отчёт', 'deadline': time(10, 0)},
    'ов': {'name': 'Вечерний отчёт', 'deadline': time(23, 59)},
    'гсд': {'name': 'Главное событие дня', 'deadline': time(23, 59)}
}

class ReportDatabase:
    """Класс для работы с базой данных отчетов"""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        """Инициализация базы данных"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS reports (
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
            conn.commit()

    def save_report(self, user_tag: str, report_type: str, day_number: int, submission_time: datetime,
                   username: str, message_id: int):
        """Сохранение отчета в базу данных"""
        dt_str = submission_time.isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO reports
                (user_tag, report_type, day_number, datetime, username, message_id)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_tag, report_type, day_number, dt_str, username, message_id))
            conn.commit()

    def get_reports_for_date(self, date: datetime) -> Dict[str, Dict[str, Dict]]:
        """Получение всех отчетов за указанную дату"""
        date_str = date.date().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT user_tag, report_type, day_number, datetime, username
                FROM reports
                WHERE date(datetime) = ?
                ORDER BY user_tag, report_type
            ''', (date_str,))

            reports = {}
            for row in cursor.fetchall():
                user_tag, report_type, day_number, dt_str, username = row
                if user_tag not in reports:
                    reports[user_tag] = {}
                reports[user_tag][report_type] = {
                    'day_number': day_number,
                    'datetime': dt_str,
                    'username': username
                }

            return reports

    def cleanup_old_reports(self, days_to_keep: int = 30):
        """Очистка старых отчетов"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        cutoff_str = cutoff_date.date().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute('DELETE FROM reports WHERE date(datetime) < ?', (cutoff_str,))
            conn.commit()

class ReportBot:
    """Основной класс бота"""

    def __init__(self):
        self.bot = Bot(token=TELEGRAM_BOT_TOKEN)
        self.dp = Dispatcher()
        self.db = ReportDatabase(DATABASE_PATH)
        self.scheduler = AsyncIOScheduler()

        # Регистрация обработчиков
        self.dp.message.register(self.handle_message, lambda msg: msg.chat.id == GROUP_CHAT_ID)
        self.dp.startup.register(self.on_startup)
        self.dp.shutdown.register(self.on_shutdown)

    async def on_startup(self):
        """Действия при запуске бота"""
        logger.info("Бот запущен")

        # Настройка планировщика
        self.scheduler.add_job(
            self.send_daily_report,
            CronTrigger(hour=0, minute=5),
            id='daily_report',
            replace_existing=True
        )
        self.scheduler.start()

        # Очистка старых данных при запуске
        self.db.cleanup_old_reports()

    async def on_shutdown(self):
        """Действия при остановке бота"""
        logger.info("Бот остановлен")
        self.scheduler.shutdown()

    def parse_message(self, text: str, username: str) -> List[Tuple[str, str, int]]:
        """Парсинг сообщения для извлечения отчетов с номерами дней"""
        reports = []
        words = text.lower().split()

        i = 0
        while i < len(words):
            word = words[i]

            # Ищем хэштег типа отчета
            if word.startswith('#') and len(word) > 3:
                # Проверяем возможные типы отчетов (2 или 3 символа)
                potential_type = None

                # Сначала пробуем 3 символа
                if word[1:4] in REPORT_TYPES:
                    potential_type = word[1:4]
                    number_part = word[4:]
                # Затем пробуем 2 символа
                elif word[1:3] in REPORT_TYPES:
                    potential_type = word[1:3]
                    number_part = word[3:]

                if potential_type and number_part.isdigit():
                    day_number = int(number_part)

                    # Ищем следующий хэштег как участника
                    participant_tag = None
                    for j in range(i + 1, len(words)):
                        next_word = words[j]
                        if next_word.startswith('#') and next_word in PARTICIPANTS.values():
                            participant_tag = next_word
                            break

                    # Если не нашли в сообщении, используем username
                    if not participant_tag and username in PARTICIPANTS:
                        participant_tag = PARTICIPANTS[username]

                    if participant_tag:
                        reports.append((potential_type, participant_tag, day_number))
                        i = j  # Пропускаем обработанный участок
                        continue

            i += 1

        return reports

    async def handle_message(self, message: types.Message):
        """Обработка входящих сообщений"""
        if not message.text:
            return

        username = f"@{message.from_user.username}" if message.from_user.username else ""
        parsed_reports = self.parse_message(message.text, username)

        if parsed_reports:
            submission_time = message.date

            for report_type, user_tag, day_number in parsed_reports:
                self.db.save_report(
                    user_tag=user_tag,
                    report_type=report_type,
                    day_number=day_number,
                    submission_time=submission_time,
                    username=username,
                    message_id=message.message_id
                )

                logger.info(f"Сохранен отчет: {user_tag} - {report_type}{day_number} в {submission_time}")

    def format_report_status(self, reports: Dict, date: datetime) -> str:
        """Форматирование статуса отчетов"""
        date_str = date.strftime("%d.%m.%Y")

        message_parts = [f"📊 **Сводка отчетов за {date_str}**\n"]

        # Определяем всех участников и создаем обратное сопоставление
        all_users = list(PARTICIPANTS.values())
        tag_to_username = {v: k for k, v in PARTICIPANTS.items()}

        # Для каждого типа отчета
        for report_type, info in REPORT_TYPES.items():
            submitted_users = []
            late_users = []
            missing_users = []

            # Проверяем дедлайн для утренних отчетов
            if report_type == 'оу':
                deadline = datetime.combine(date.date(), info['deadline'])
            else:
                deadline = datetime.combine(date.date(), info['deadline'])

            for user_tag in all_users:
                if user_tag in reports and report_type in reports[user_tag]:
                    submission_time = datetime.fromisoformat(reports[user_tag][report_type]['datetime'])
                    day_number = reports[user_tag][report_type]['day_number']

                    # Проверяем, был ли отчет сдан вовремя
                    if report_type == 'оу' and submission_time.time() > info['deadline']:
                        late_users.append(f"{tag_to_username.get(user_tag, user_tag)}({day_number})")
                    else:
                        submitted_users.append(f"{tag_to_username.get(user_tag, user_tag)}({day_number})")
                else:
                    # Определяем, пропущен ли дедлайн
                    if report_type == 'оу':
                        if datetime.now().time() > info['deadline']:
                            missing_users.append(tag_to_username.get(user_tag, user_tag))
                    else:
                        # Для вечерних отчетов дедлайн в 23:59
                        if datetime.now().date() > date.date():
                            missing_users.append(tag_to_username.get(user_tag, user_tag))

            # Форматируем результат для типа отчета
            emoji = {'ос': '🏃', 'оу': '🌅', 'ов': '🌙', 'гсд': '⭐'}[report_type]
            message_parts.append(f"\n{emoji} **{info['name']}:**")

            if submitted_users:
                message_parts.append(f"✅ Вовремя: {', '.join(submitted_users)}")

            if late_users:
                message_parts.append(f"⚠️ Опоздали: {', '.join(late_users)}")

            if missing_users:
                message_parts.append(f"❌ Не сдали: {', '.join(missing_users)}")

        return "\n".join(message_parts)

    async def send_daily_report(self):
        """Отправка ежедневной сводки"""
        try:
            yesterday = datetime.now() - timedelta(days=1)
            reports = self.db.get_reports_for_date(yesterday)

            report_message = self.format_report_status(reports, yesterday)

            await self.bot.send_message(
                chat_id=GROUP_CHAT_ID,
                text=report_message,
                parse_mode="Markdown"
            )

            logger.info(f"Отправлена сводка за {yesterday.strftime('%d.%m.%Y')}")

        except Exception as e:
            logger.error(f"Ошибка при отправке ежедневной сводки: {e}")

    async def handle_help(self, message: types.Message):
        """Обработка команды /help"""
        await message.reply(
            "📋 **Формат отчетов:**\n"
            "`#типномер #участник`\n\n"
            "🏷️ **Типы отчетов:**\n"
            "• `ос` - Спорт\n"
            "• `оу` - Утренний отчёт\n" 
            "• `ов` - Вечерний отчёт\n"
            "• `гсд` - Главное событие дня\n\n"
            "👥 **Участники:**\n"
            "@A_N_yaki → #ан\n"
            "@Dev_Jones → #ден\n"
            "@FenolIFtalein → #никита\n"
            "@Igor_Lucklett → #игорь\n"
            "@Melnikova_Alena → #ал\n"
            "@Mikhailovmind → #тор\n"
            "@Polyhakayna0 → #поли\n"
            "@Wlad_is_law → #в\n"
            "@bleffucio → #арк\n"
            "@helga_sigy → #оля\n"
            "@mix_nastya → #нася\n"
            "@nadezhda_efremova123 → #надя\n"
            "@travellove_krd → #любовь\n\n"
            "📅 **Пример:**\n"
            "`#ос100 #тор` = спорт за 100-й день от @Mikhailovmind"
        )

    async def run(self):
        """Запуск бота"""
        # Регистрация обработчиков
        self.dp.message.register(self.handle_start, Command("start"))
        self.dp.message.register(self.handle_help, Command("help"))
        self.dp.message.register(self.handle_message)

        try:
            await self.dp.start_polling(self.bot)
        except Exception as e:
            logger.error(f"Ошибка при запуске бота: {e}")
        finally:
            await self.bot.session.close()

async def main():
    """Главная функция"""
    bot = ReportBot()
    await bot.run()

if __name__ == "__main__":
    asyncio.run(main())
