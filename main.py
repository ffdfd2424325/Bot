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
REPORTS_TOPIC_ID = os.getenv('REPORTS_TOPIC_ID') or None
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

# Типы отчетов и их дедлайны
REPORT_TYPES = {
    '#оу': {'name': 'Утренний отчёт', 'deadline': time(10, 0)},
    '#ос': {'name': 'Спорт', 'deadline': time(23, 59)},
    '#ов': {'name': 'Вечерний отчёт', 'deadline': time(23, 59)},
    '#гсд': {'name': 'Главное событие дня', 'deadline': time(23, 59)}
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
                    report_date DATE NOT NULL,
                    submission_time TIME NOT NULL,
                    username TEXT,
                    message_id INTEGER,
                    UNIQUE(user_tag, report_type, report_date)
                )
            ''')
            conn.commit()

    def save_report(self, user_tag: str, report_type: str, submission_time: datetime,
                   username: str, message_id: int):
        """Сохранение отчета в базу данных"""
        date_str = submission_time.date().isoformat()
        time_str = submission_time.time().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO reports
                (user_tag, report_type, report_date, submission_time, username, message_id)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_tag, report_type, date_str, time_str, username, message_id))
            conn.commit()

    def get_reports_for_date(self, date: datetime) -> Dict[str, Dict[str, Dict]]:
        """Получение всех отчетов за указанную дату"""
        date_str = date.date().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute('''
                SELECT user_tag, report_type, submission_time, username
                FROM reports
                WHERE report_date = ?
                ORDER BY user_tag, report_type
            ''', (date_str,))

            reports = {}
            for row in cursor.fetchall():
                user_tag, report_type, time_str, username = row
                if user_tag not in reports:
                    reports[user_tag] = {}
                reports[user_tag][report_type] = {
                    'time': time_str,
                    'username': username
                }

            return reports

    def cleanup_old_reports(self, days_to_keep: int = 30):
        """Очистка старых отчетов"""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        cutoff_str = cutoff_date.date().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            conn.execute('DELETE FROM reports WHERE report_date < ?', (cutoff_str,))
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

    def parse_message(self, text: str, username: str) -> List[Tuple[str, str]]:
        """Парсинг сообщения для извлечения отчетов"""
        reports = []
        words = text.lower().split()

        for word in words:
            if word.startswith('#') and len(word) > 1:
                # Проверяем, является ли это типом отчета
                if word[:3] in REPORT_TYPES:
                    report_type = word[:3]

                    # Ищем соответствующий тег участника
                    participant_tag = None
                    for tag in words:
                        if tag in PARTICIPANTS.values():
                            participant_tag = tag
                            break

                    # Если тег участника не найден в сообщении, используем username
                    if not participant_tag and username in PARTICIPANTS:
                        participant_tag = PARTICIPANTS[username]

                    if participant_tag:
                        reports.append((report_type, participant_tag))

        return reports

    async def handle_message(self, message: types.Message):
        """Обработка входящих сообщений"""
        if not message.text:
            return

        username = f"@{message.from_user.username}" if message.from_user.username else ""
        parsed_reports = self.parse_message(message.text, username)

        if parsed_reports:
            submission_time = message.date

            for report_type, user_tag in parsed_reports:
                self.db.save_report(
                    user_tag=user_tag,
                    report_type=report_type,
                    submission_time=submission_time,
                    username=username,
                    message_id=message.message_id
                )

                logger.info(f"Сохранен отчет: {user_tag} - {report_type} в {submission_time}")

    def format_report_status(self, reports: Dict, date: datetime) -> str:
        """Форматирование статуса отчетов"""
        date_str = date.strftime("%d.%m.%Y")

        message_parts = [f"📊 **Сводка отчетов за {date_str}**\n"]

        # Определяем всех участников
        all_users = list(PARTICIPANTS.values())

        # Для каждого типа отчета
        for report_type, info in REPORT_TYPES.items():
            submitted_users = []
            late_users = []
            missing_users = []

            # Проверяем дедлайн для утренних отчетов
            if report_type == '#оу':
                deadline = datetime.combine(date.date(), info['deadline'])
            else:
                deadline = datetime.combine(date.date(), info['deadline'])

            for user_tag in all_users:
                if user_tag in reports and report_type in reports[user_tag]:
                    submission_time = datetime.fromisoformat(reports[user_tag][report_type]['time'])

                    # Проверяем, был ли отчет сдан вовремя
                    if report_type == '#оу' and submission_time.time() > info['deadline']:
                        late_users.append(user_tag)
                    else:
                        submitted_users.append(user_tag)
                else:
                    # Определяем, пропущен ли дедлайн
                    if report_type == '#оу':
                        if datetime.now().time() > info['deadline']:
                            missing_users.append(user_tag)
                    else:
                        # Для вечерних отчетов дедлайн в 23:59
                        if datetime.now().date() > date.date():
                            missing_users.append(user_tag)

            # Форматируем результат для типа отчета
            emoji = {'#оу': '🌅', '#ос': '🏃', '#ов': '🌙', '#гсд': '⭐'}[report_type]
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

    async def run(self):
        """Запуск бота"""
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
