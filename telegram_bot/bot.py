"""
Telegram бот для генерации поздравительных изображений через GigaChat API

Использование:
1. Создайте бота через @BotFather в Telegram
2. Получите токен бота
3. Добавьте TELEGRAM_BOT_TOKEN в .env файл
4. Запустите: python telegram_bot/bot.py
"""
import os
import sys
import asyncio
import secrets
import string
import hashlib
from pathlib import Path
from typing import Dict, Optional, List
from datetime import datetime

# Добавляем корневую директорию проекта в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from gigachat_module.prompt import generate_greeting_image
from gigachat_module.text_generator import generate_greeting_text
from database import Database


class GreetingBot:
    """Telegram бот для генерации поздравительных изображений"""
    
    def __init__(self, token: str):
        """Инициализация бота"""
        self.token = token
        self.application = Application.builder().token(token).build()
        self.db = Database()
        self.scheduler = None  # Будет создан в post_init
        
        # Загружаем список админов из переменных окружения
        admin_ids_str = os.getenv("TELEGRAM_ADMIN_IDS", "")
        self.admin_ids = [int(uid.strip()) for uid in admin_ids_str.split(",") if uid.strip()] if admin_ids_str else []
        
        # Состояние бота: режим работы и текущая дата
        self.auto_mode = True  # True - автоматический режим (+), False - ручной режим (-)
        self.current_date = None  # Установленная дата (если режим ручной)
        
        self._setup_handlers()
        # Настраиваем post_init для создания и запуска планировщика после инициализации event loop
        self.application.post_init = self._post_init
    
    async def _post_init(self, application: Application) -> None:
        """Вызывается после инициализации event loop"""
        # Создаем и запускаем планировщик после инициализации event loop
        self.scheduler = AsyncIOScheduler()
        self._setup_scheduler()
        self.scheduler.start()
        print("📅 Планировщик автоматических поздравлений активирован (проверка каждый день в 9:00)")
    
    def _setup_handlers(self):
        """Настройка обработчиков команд"""
        # Обработчик команды /start
        start_handler = CommandHandler("start", self.start_command)
        
        # Обработчик текстовых сообщений от админов (управление датой и режимом)
        admin_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_admin_message)
        
        self.application.add_handler(start_handler)
        self.application.add_handler(admin_handler)
    
    def _is_admin(self, user_id: int) -> bool:
        """Проверяет, является ли пользователь админом"""
        return user_id in self.admin_ids
    
    def _generate_referral_code(self, user_data: Dict, length: int = 11) -> str:
        """
        Генерирует уникальный реферальный код на основе личных данных пользователя
        
        Использует метод из Database для генерации кода с проверкой уникальности.
        
        Args:
            user_data: Словарь с данными пользователя (id, name, birth_date, start_date_bank)
            length: Длина кода (10-12 символов, по умолчанию 11)
        
        Returns:
            Строка с уникальным реферальным кодом
        """
        return self.db.generate_unique_referral_code(user_data, length)
    
    def _find_user_by_referral_code(self, referral_code: str, check_used: bool = True) -> Optional[Dict]:
        """
        Находит пользователя по реферальному коду
        
        Args:
            referral_code: Реферальный код для поиска
            check_used: Проверять ли, был ли код уже использован (если True, вернет None для использованных кодов)
        
        Returns:
            Словарь с данными пользователя или None, если не найден или уже использован
        """
        try:
            user = self.db.get_user_by_referral_code(referral_code)
            if not user:
                return None
            
            # Если нужно проверить использование и код уже использован (есть chat_id)
            if check_used:
                chat_id = user.get('telegram_chat_id')
                if chat_id:
                    # Код уже использован
                    return None
            
            return user
        except Exception as e:
            print(f"[ERROR] Ошибка поиска пользователя по реферальному коду: {e}")
            return None
    
    def _is_referral_code_used(self, referral_code: str) -> bool:
        """Проверяет, был ли реферальный код уже использован"""
        try:
            user = self.db.get_user_by_referral_code(referral_code)
            if not user:
                return False
            chat_id = user.get('telegram_chat_id')
            return bool(chat_id)
        except Exception as e:
            print(f"[ERROR] Ошибка проверки использования реферального кода: {e}")
            return False
    
    def _save_user_chat_id(self, referral_code: Optional[str] = None, chat_id: Optional[int] = None, 
                          user_id: Optional[int] = None):
        """
        Сохраняет chat_id пользователя в базу данных
        
        Args:
            referral_code: Реферальный код пользователя (приоритетный способ поиска)
            chat_id: Chat ID пользователя в Telegram
            user_id: User ID пользователя (резервный способ поиска)
        """
        try:
            success = self.db.update_user_chat_id(
                referral_code=referral_code,
                chat_id=chat_id,
                user_id=user_id
            )
            
            if success:
                # Получаем имя пользователя для логирования
                if referral_code:
                    user = self.db.get_user_by_referral_code(referral_code)
                elif user_id:
                    user = self.db.get_user_by_chat_id(chat_id) if chat_id else None
                else:
                    user = None
                
                user_name = user.get('name', 'Unknown') if user else 'Unknown'
                print(f"[INFO] Сохранен chat_id {chat_id} для пользователя {user_name} (код: {referral_code or 'N/A'})")
            
            return success
        except Exception as e:
            print(f"[WARNING] Не удалось сохранить chat_id: {e}")
            return False
    
    def _setup_scheduler(self):
        """Настройка планировщика задач для автоматической отправки поздравлений"""
        # Проверяем праздники каждый день в 9:00 утра
        # Используем 'async' executor для async функций
        self.scheduler.add_job(
            self.check_and_send_greetings,
            CronTrigger(hour=9, minute=0),
            id='daily_greetings',
            name='Ежедневная проверка и отправка поздравлений',
            executor='default'
        )
    
    def _get_current_date(self) -> str:
        """Получает текущую дату в зависимости от режима"""
        if self.auto_mode:
            # Автоматический режим - используем текущую дату
            return datetime.now().strftime("%d.%m.%Y")
        else:
            # Ручной режим - используем установленную дату
            if self.current_date:
                return self.current_date
            else:
                # Если дата не установлена, используем текущую
                return datetime.now().strftime("%d.%m.%Y")
    
    async def check_and_send_greetings(self):
        """Проверяет праздники и дни рождения на текущую дату и отправляет поздравления"""
        current_date = self._get_current_date()
        print(f"[INFO] Проверка праздников на {current_date} (режим: {'автоматический' if self.auto_mode else 'ручной'})...")
        
        await self.check_and_send_greetings_for_date(current_date)
    
    async def check_and_send_greetings_for_date(self, date_str: str):
        """Проверяет праздники и дни рождения на указанную дату и отправляет поздравления"""
        # Конвертируем дату в нужные форматы
        try:
            date_obj = datetime.strptime(date_str, "%d.%m.%Y")
            date_yyyy_mm_dd = date_obj.strftime("%Y-%m-%d")
            date_dd_mm = date_obj.strftime("%d.%m")
        except ValueError:
            print(f"[ERROR] Неверный формат даты: {date_str}")
            return
        
        # Получаем дни рождения на эту дату
        birthdays = self.db.get_users_by_birthday(date_dd_mm)
        
        # Получаем праздники на эту дату
        holidays = self.db.get_holidays_by_date(date_yyyy_mm_dd)
        
        # Обрабатываем дни рождения
        for user in birthdays:
            chat_id = user.get('telegram_chat_id', '').strip()
            
            # Используем только chat_id
            if not chat_id:
                print(f"[WARNING] Пропущен пользователь {user.get('name', 'Unknown')}: нет chat_id (пользователь не активирован)")
                continue
            
            try:
                await self.send_birthday_greeting(user, chat_id, date_str)
            except Exception as e:
                print(f"[ERROR] Ошибка отправки поздравления с днем рождения пользователю {chat_id}: {e}")
        
        # Обрабатываем праздники
        users_by_holiday = {}
        for holiday in holidays:
            holiday_id = holiday.get('id', '')
            users = self.db.get_users_for_holiday(holiday, date_yyyy_mm_dd)
            users_by_holiday[holiday_id] = users
        
        for holiday in holidays:
            holiday_id = holiday.get('id', '')
            users = users_by_holiday.get(holiday_id, [])
            
            for user in users:
                chat_id = user.get('telegram_chat_id', '').strip()
                
                # Используем только chat_id
                if not chat_id:
                    print(f"[WARNING] Пропущен пользователь {user.get('name', 'Unknown')}: нет chat_id (пользователь не активирован)")
                    continue
                
                try:
                    await self.send_holiday_greeting(user, holiday, chat_id, date_str)
                except Exception as e:
                    print(f"[ERROR] Ошибка отправки поздравления с праздником пользователю {chat_id}: {e}")
        
        print(f"[INFO] Проверка завершена. Обработано {len(birthdays)} дней рождения и {len(holidays)} праздников.")
    
    async def send_birthday_greeting(self, user: Dict, chat_id_or_username: str, event_date_str: str):
        """Отправляет поздравление с днем рождения пользователю"""
        # Извлекаем данные пользователя
        name = user.get('name', '')
        birth_date = user.get('birth_date', '')
        user_type = user.get('user_type', 'client')
        interests = user.get('interests', '')
        
        # Определяем сегмент на основе типа пользователя
        client_segment = "VIP" if user_type == "employee" else "лояльный"
        
        # Используем переданную дату события
        event_date = event_date_str
        
        # Генерируем поздравление
        try:
            # Генерируем текст
            greeting_text = generate_greeting_text(
                event_date=event_date,
                event_type="день рождения",
                client_name=name,
                client_segment=client_segment,
                tone="дружеский",
                preferences=[interests] if interests else None,
                evaluate_sincerity=True,
                min_sincerity=0.6
            )
            
            # Генерируем изображение
            output_dir = Path(__file__).parent.parent / "output" / "telegram" / "auto"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name_safe = name.replace(" ", "_")
            output_path = output_dir / f"birthday_{name_safe}_{timestamp}.png"
            
            image_path = generate_greeting_image(
                output_path=str(output_path),
                event_date=event_date,
                event_type="день рождения",
                client_name=name,
                client_segment=client_segment,
                tone="дружеский",
                preferences=[interests] if interests else None
            )
            
            # Отправляем сообщение пользователю
            # Отправляем изображение с текстом
            with open(image_path, "rb") as photo:
                max_length = 1024 - 10
                caption = greeting_text[:max_length-3] + "..." if len(greeting_text) > max_length else greeting_text
                
                try:
                    # Определяем chat_id: если это число, используем как есть, иначе добавляем @
                    if chat_id_or_username.isdigit():
                        chat_id = int(chat_id_or_username)
                    else:
                        chat_id = f"@{chat_id_or_username}"
                    
                    await self.application.bot.send_photo(
                        chat_id=chat_id,
                        photo=photo,
                        caption=caption,
                        parse_mode="HTML"
                    )
                    print(f"[INFO] ✅ Отправлено поздравление с днем рождения пользователю {chat_id}")
                except Exception as send_error:
                    error_msg = str(send_error).lower()
                    if "chat not found" in error_msg or "user not found" in error_msg:
                        print(f"[WARNING] Пользователь {chat_id_or_username} не найден или не начал диалог с ботом")
                    else:
                        print(f"[ERROR] Ошибка отправки сообщения пользователю {chat_id_or_username}: {send_error}")
                    raise
            
        except Exception as e:
            print(f"[ERROR] Ошибка генерации поздравления с днем рождения для {chat_id_or_username}: {e}")
            # Не пробрасываем исключение дальше, чтобы не прерывать обработку других пользователей
    
    async def send_holiday_greeting(self, user: Dict, holiday: Dict, chat_id_or_username: str, event_date_str: str):
        """Отправляет поздравление с праздником пользователю"""
        # Извлекаем данные
        name = user.get('name', '')
        user_type = user.get('user_type', 'client')
        position = user.get('position', '')
        interests = user.get('interests', '')
        
        holiday_name = holiday.get('holiday_name', '')
        
        # Определяем сегмент
        client_segment = "VIP" if user_type == "employee" else "лояльный"
        
        # Используем переданную дату события
        event_date = event_date_str
        
        # Определяем тон в зависимости от праздника
        tone = "официальный"
        if "женский день" in holiday_name.lower() or "8" in holiday_name:
            tone = "дружеский"
        elif "новый год" in holiday_name.lower():
            tone = "креативный"
        
        try:
            # Генерируем текст
            greeting_text = generate_greeting_text(
                event_date=event_date,
                event_type=holiday_name,
                client_name=name,
                position=position if position else None,
                client_segment=client_segment,
                tone=tone,
                preferences=[interests] if interests else None,
                evaluate_sincerity=True,
                min_sincerity=0.6
            )
            
            # Генерируем изображение
            output_dir = Path(__file__).parent.parent / "output" / "telegram" / "auto"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            name_safe = name.replace(" ", "_")
            holiday_safe = holiday_name.replace(" ", "_").replace("/", "_")
            output_path = output_dir / f"holiday_{holiday_safe}_{name_safe}_{timestamp}.png"
            
            image_path = generate_greeting_image(
                output_path=str(output_path),
                event_date=event_date,
                event_type=holiday_name,
                client_name=name,
                position=position if position else None,
                client_segment=client_segment,
                tone=tone,
                preferences=[interests] if interests else None
            )
            
            # Отправляем сообщение пользователю
            # Отправляем изображение с текстом
            with open(image_path, "rb") as photo:
                max_length = 1024 - 10
                caption = greeting_text[:max_length-3] + "..." if len(greeting_text) > max_length else greeting_text
                
                try:
                    # Определяем chat_id: если это число, используем как есть, иначе добавляем @
                    if chat_id_or_username.isdigit():
                        chat_id = int(chat_id_or_username)
                    else:
                        chat_id = f"@{chat_id_or_username}"
                    
                    await self.application.bot.send_photo(
                        chat_id=chat_id,
                        photo=photo,
                        caption=caption,
                        parse_mode="HTML"
                    )
                    print(f"[INFO] ✅ Отправлено поздравление с праздником '{holiday_name}' пользователю {chat_id}")
                except Exception as send_error:
                    error_msg = str(send_error).lower()
                    if "chat not found" in error_msg or "user not found" in error_msg:
                        print(f"[WARNING] Пользователь {chat_id_or_username} не найден или не начал диалог с ботом")
                    else:
                        print(f"[ERROR] Ошибка отправки сообщения пользователю {chat_id_or_username}: {send_error}")
                    raise
            
        except Exception as e:
            print(f"[ERROR] Ошибка генерации поздравления с праздником для {chat_id_or_username}: {e}")
            # Не пробрасываем исключение дальше, чтобы не прерывать обработку других пользователей
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /start с поддержкой реферальных кодов"""
        user = update.effective_user
        user_id = user.id
        chat_id = update.effective_chat.id
        
        # Получаем реферальный код из параметров команды (deep linking: /start CODE)
        referral_code = None
        if context.args and len(context.args) > 0:
            referral_code = context.args[0].strip()
        
        # Если есть реферальный код, ищем пользователя и сохраняем chat_id
        if referral_code:
            # Проверяем, был ли код уже использован
            if self._is_referral_code_used(referral_code):
                await update.message.reply_text(
                    "❌ Этот реферальный код уже был использован.\n\n"
                    "Каждый код можно использовать только один раз.\n"
                    "Обратитесь к администратору за новым кодом."
                )
                return
            
            # Ищем пользователя по коду (проверяем, что код не использован)
            user_data = self._find_user_by_referral_code(referral_code, check_used=True)
            if user_data:
                # Сохраняем chat_id для найденного пользователя
                success = self._save_user_chat_id(
                    referral_code=referral_code,
                    chat_id=chat_id
                )
                
                if success:
                    user_name = user_data.get('name', 'Пользователь')
                    welcome_text = (
                        f"Привет, {user.first_name}! 👋\n\n"
                        f"Вы успешно активированы как {user_name}.\n\n"
                        f"Бот будет автоматически отправлять вам поздравления в дни ваших праздников.\n\n"
                        f"✅ Реферальный код активирован и больше не может быть использован."
                    )
                    await update.message.reply_text(welcome_text, parse_mode="Markdown")
                    return
                else:
                    await update.message.reply_text(
                        "❌ Ошибка при активации кода. Попробуйте позже или обратитесь к администратору."
                    )
                    return
            else:
                # Неверный реферальный код
                await update.message.reply_text(
                    "❌ Неверный реферальный код.\n\n"
                    "Пожалуйста, используйте ссылку, предоставленную вам администратором."
                )
                return
        
        # Если нет реферального кода, проверяем админа
        if self._is_admin(user_id):
            # Админы могут использовать бот без реферального кода
            self._save_user_chat_id(user_id=user_id, chat_id=chat_id)
            welcome_text = (
                f"Привет, {user.first_name}! 👋\n\n"
                f"Вы администратор бота.\n\n"
                f"**Доступные команды:**\n\n"
                f"📅 **Установить дату:** отправьте дату в формате DD.MM.YYYY\n"
                f"   Пример: 01.01.2025\n\n"
                f"➕ **Автоматический режим:** отправьте +\n"
                f"   Бот будет использовать текущую дату\n\n"
                f"➖ **Ручной режим:** отправьте -\n"
                f"   Бот будет использовать установленную дату\n\n"
                f"**Текущий режим:** {'Автоматический (+)' if self.auto_mode else 'Ручной (-)'}\n"
            )
            if not self.auto_mode and self.current_date:
                welcome_text += f"**Установленная дата:** {self.current_date}\n"
            else:
                welcome_text += f"**Текущая дата:** {datetime.now().strftime('%d.%m.%Y')}\n"
        else:
            # Обычный пользователь без реферального кода
            welcome_text = (
                f"Привет, {user.first_name}! 👋\n\n"
                f"Для использования бота вам необходим реферальный код.\n\n"
                f"Пожалуйста, используйте ссылку, предоставленную вам администратором.\n\n"
                f"Формат ссылки: `t.me/ваш_бот?start=КОД`"
            )
        
        await update.message.reply_text(welcome_text, parse_mode="Markdown")
    
    async def handle_admin_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка сообщений от админов"""
        user = update.effective_user
        user_id = user.id
        
        # Проверяем, является ли пользователь админом
        # Если не админ - просто игнорируем сообщение без ответа
        if not self._is_admin(user_id):
            return
        
        text = update.message.text.strip()
        
        # Обработка команд
        if text == "+":
            # Автоматический режим
            self.auto_mode = True
            self.current_date = None
            await update.message.reply_text(
                "✅ **Автоматический режим активирован**\n\n"
                f"Бот будет использовать текущую дату: {datetime.now().strftime('%d.%m.%Y')}"
            )
            return
        
        elif text == "-":
            # Ручной режим
            self.auto_mode = False
            if self.current_date:
                await update.message.reply_text(
                    f"✅ **Ручной режим активирован**\n\n"
                    f"Текущая установленная дата: {self.current_date}\n\n"
                    f"Отправьте дату в формате DD.MM.YYYY для установки новой даты."
                )
            else:
                await update.message.reply_text(
                    "✅ **Ручной режим активирован**\n\n"
                    "Отправьте дату в формате DD.MM.YYYY для установки даты."
                )
            return
        
        # Проверяем, является ли сообщение датой в формате DD.MM.YYYY
        try:
            parsed_date = datetime.strptime(text, "%d.%m.%Y")
            # Устанавливаем дату
            self.current_date = text
            self.auto_mode = False  # При установке даты автоматически переключаемся в ручной режим
            
            # Проверяем праздники на эту дату и отправляем поздравления
            await update.message.reply_text(
                f"✅ **Дата установлена:** {text}\n"
                f"**Режим:** Ручной (-)\n\n"
                f"🔍 Проверяю праздники на эту дату..."
            )
            
            # Отправляем поздравления
            await self.check_and_send_greetings_for_date(text)
            
            await update.message.reply_text("✅ Проверка завершена! См. логи для деталей.")
            
        except ValueError:
            # Не является датой
            await update.message.reply_text(
                "❌ Неверный формат команды.\n\n"
                "**Доступные команды:**\n"
                "• `+` - автоматический режим\n"
                "• `-` - ручной режим\n"
                "• `DD.MM.YYYY` - установить дату (например: 01.01.2025)",
                parse_mode="Markdown"
            )
    
    def run(self):
        """Запуск бота"""
        print("🤖 Бот запущен! Нажмите Ctrl+C для остановки.")
        
        try:
            # Запускаем бота (планировщик запустится через post_init после создания event loop)
            self.application.run_polling(allowed_updates=Update.ALL_TYPES)
        finally:
            # Останавливаем планировщик при остановке бота
            if self.scheduler and self.scheduler.running:
                self.scheduler.shutdown()


def main():
    """Главная функция"""
    # Получаем токен из переменных окружения
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    
    if not token:
        print("❌ Ошибка: не найден TELEGRAM_BOT_TOKEN в переменных окружения или .env файле")
        print("\nДля получения токена:")
        print("1. Откройте Telegram и найдите @BotFather")
        print("2. Отправьте команду /newbot")
        print("3. Следуйте инструкциям для создания бота")
        print("4. Скопируйте полученный токен")
        print("5. Добавьте в .env файл: TELEGRAM_BOT_TOKEN=ваш_токен")
        return
    
    # Проверяем наличие админов
    admin_ids_str = os.getenv("TELEGRAM_ADMIN_IDS", "")
    if not admin_ids_str:
        print("⚠️  Внимание: TELEGRAM_ADMIN_IDS не установлен в .env файле")
        print("\nДля получения ID пользователя:")
        print("1. Найдите бота @userinfobot в Telegram")
        print("2. Отправьте ему любое сообщение")
        print("3. Скопируйте ваш ID (число)")
        print("4. Добавьте в .env файл: TELEGRAM_ADMIN_IDS=ваш_id")
        print("\nДля нескольких админов используйте запятую: TELEGRAM_ADMIN_IDS=123456789,987654321")
        print("\nБот будет работать, но только админы смогут управлять датой.")
    
    # Создаем и запускаем бота
    bot = GreetingBot(token)
    bot.run()


if __name__ == "__main__":
    main()
