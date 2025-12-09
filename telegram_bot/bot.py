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
from pathlib import Path
from typing import Dict, Optional
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
from gigachat_module.prompt import generate_greeting_image
from gigachat_module.text_generator import generate_greeting_text


class GreetingBot:
    """Telegram бот для генерации поздравительных изображений"""
    
    def __init__(self, token: str):
        """Инициализация бота"""
        self.token = token
        self.application = Application.builder().token(token).build()
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Настройка обработчиков команд"""
        # Обработчик команды /start
        start_handler = CommandHandler("start", self.start_command)
        
        # Обработчик команды /generate
        generate_handler = CommandHandler("generate", self.generate_command)
        
        # Обработчик текстовых сообщений (данные для генерации)
        data_handler = MessageHandler(filters.TEXT & ~filters.COMMAND, self.process_data)
        
        self.application.add_handler(start_handler)
        self.application.add_handler(generate_handler)
        self.application.add_handler(data_handler)
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка команды /start"""
        user = update.effective_user
        welcome_text = (
            f"Привет, {user.first_name}! 👋\n\n"
            f"Я бот для генерации персонализированных поздравительных изображений.\n\n"
            f"Используй команду /generate чтобы увидеть формат ввода данных.\n\n"
            f"Затем отправь все данные одним сообщением, разделяя их переносами строк."
        )
        await update.message.reply_text(welcome_text)
    
    async def generate_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Показ формата ввода данных"""
        format_text = (
            "📝 **Формат ввода данных:**\n\n"
            "Отправьте все данные одним сообщением, разделяя их переносами строк:\n\n"
            "1️⃣ **Дата события** (обязательно, формат DD.MM.YYYY)\n"
            "   Пример: 01.01.2025\n\n"
            "2️⃣ **Имя клиента** (опционально, можно оставить пустым)\n"
            "   Пример: Иван Петров\n\n"
            "3️⃣ **Название компании** (опционально)\n"
            "   Пример: ООО 'ТехноСтрой'\n\n"
            "4️⃣ **Должность** (опционально)\n"
            "   Пример: Генеральный директор\n\n"
            "5️⃣ **Сегмент клиента** (опционально: VIP, новый, лояльный, стандартный)\n"
            "   Пример: VIP\n\n"
            "6️⃣ **Тон** (опционально: официальный, дружеский, креативный)\n"
            "   Пример: официальный\n\n"
            "7️⃣ **Предпочтения** (опционально, через запятую)\n"
            "   Пример: премиум качество, корпоративный стиль\n\n"
            "8️⃣ **Тип события/праздника** (обязательно)\n"
            "   Укажите любой тип события или праздника в свободной форме\n"
            "   Примеры: новый год, день рождения, 8 марта, профессиональный праздник, юбилей, день компании\n\n"
            "**Пример полного сообщения:**\n"
            "```\n"
            "01.01.2025\n"
            "Иван Петров\n"
            "ООО 'ТехноСтрой'\n"
            "Генеральный директор\n"
            "VIP\n"
            "официальный\n"
            "премиум качество, корпоративный стиль\n"
            "новый год\n"
            "```\n\n"
            "💡 **Совет:** Если какое-то поле не нужно, просто оставьте пустую строку."
        )
        await update.message.reply_text(format_text, parse_mode="Markdown")
    
    def _parse_data(self, text: str) -> Dict:
        """Парсинг данных из текста, разделенного переносами строк"""
        lines = [line.strip() for line in text.split('\n')]
        
        data = {}
        
        # 1. Дата события (обязательно)
        if len(lines) > 0 and lines[0]:
            try:
                datetime.strptime(lines[0], "%d.%m.%Y")
                data["event_date"] = lines[0]
            except ValueError:
                raise ValueError(f"Неверный формат даты: {lines[0]}. Используйте формат DD.MM.YYYY")
        else:
            raise ValueError("Дата события обязательна для заполнения")
        
        # 2. Имя клиента (опционально)
        if len(lines) > 1 and lines[1]:
            data["client_name"] = lines[1]
        
        # 3. Название компании (опционально)
        if len(lines) > 2 and lines[2]:
            data["company_name"] = lines[2]
        
        # 4. Должность (опционально)
        if len(lines) > 3 and lines[3]:
            data["position"] = lines[3]
        
        # 5. Сегмент клиента (опционально)
        if len(lines) > 4 and lines[4]:
            segment = lines[4].lower()
            valid_segments = ["vip", "новый", "лояльный", "стандартный"]
            if segment in valid_segments:
                data["client_segment"] = segment
            else:
                data["client_segment"] = "стандартный"
        else:
            data["client_segment"] = "стандартный"
        
        # 6. Тон (опционально)
        if len(lines) > 5 and lines[5]:
            tone = lines[5].lower()
            valid_tones = ["официальный", "дружеский", "креативный"]
            if tone in valid_tones:
                data["tone"] = tone
            else:
                data["tone"] = "официальный"
        else:
            data["tone"] = "официальный"
        
        # 7. Предпочтения (опционально)
        if len(lines) > 6 and lines[6]:
            preferences = [p.strip() for p in lines[6].split(",") if p.strip()]
            if preferences:
                data["preferences"] = preferences
        
        # 8. Тип события/праздника (обязательно) - принимается любой текст
        if len(lines) > 7 and lines[7]:
            # Принимаем любой текст как тип события (в свободной форме)
            data["event_type"] = lines[7].strip()
        else:
            raise ValueError("Тип события/праздника обязателен для заполнения (8-й параметр)")
        
        return data
    
    async def process_data(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка данных для генерации изображения"""
        text = update.message.text.strip()
        
        # Пропускаем команды
        if text.startswith('/'):
            return
        
        # Парсим данные
        try:
            data = self._parse_data(text)
        except ValueError as e:
            await update.message.reply_text(
                f"❌ Ошибка в формате данных: {e}\n\n"
                f"Используйте команду /generate чтобы увидеть правильный формат."
            )
            return
        
        # Проверяем обязательное поле
        if "event_date" not in data:
            await update.message.reply_text(
                "❌ Ошибка: не указана дата события\n\n"
                "Используйте команду /generate чтобы увидеть правильный формат."
            )
            return
        
        # Генерируем текст и изображение
        await update.message.reply_text("🎨 Генерирую поздравление... Это может занять некоторое время...")
        
        try:
            # Создаем уникальное имя файла
            output_dir = Path(__file__).parent.parent / "output" / "telegram"
            output_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            client_name_safe = data.get("client_name", "client").replace(" ", "_")
            output_path = output_dir / f"{client_name_safe}_{timestamp}.png"
            
            # Генерируем текст поздравления
            greeting_text = None
            try:
                greeting_text = generate_greeting_text(
                    event_date=data["event_date"],
                    event_type=data.get("event_type"),
                    client_name=data.get("client_name"),
                    company_name=data.get("company_name"),
                    position=data.get("position"),
                    client_segment=data.get("client_segment", "стандартный"),
                    tone=data.get("tone", "официальный"),
                    preferences=data.get("preferences"),
                    interaction_history=data.get("interaction_history")
                )
            except Exception as text_error:
                print(f"[ERROR] Text generation failed: {text_error}")
                # Продолжаем генерацию изображения даже если текст не сгенерировался
                greeting_text = "Поздравляем с праздником!"
            
            # Генерируем изображение
            image_path = generate_greeting_image(
                output_path=str(output_path),
                event_date=data["event_date"],
                event_type=data.get("event_type"),
                client_name=data.get("client_name"),
                company_name=data.get("company_name"),
                position=data.get("position"),
                client_segment=data.get("client_segment", "стандартный"),
                tone=data.get("tone", "официальный"),
                preferences=data.get("preferences"),
                interaction_history=data.get("interaction_history")
            )
            
            # Отправляем изображение с текстом в подписи
            with open(image_path, "rb") as photo:
                caption = "✅ Поздравительное изображение сгенерировано!"
                if greeting_text:
                    # Ограничиваем длину подписи (Telegram ограничивает до 1024 символов)
                    # Берем полный текст, но обрезаем если слишком длинный
                    max_length = 1024 - 10  # Оставляем запас
                    if len(greeting_text) > max_length:
                        caption = greeting_text[:max_length-3] + "..."
                    else:
                        caption = greeting_text
                
                await update.message.reply_photo(
                    photo=photo,
                    caption=caption
                )
            
        except Exception as e:
            # Пишем ошибку в логи для отладки
            import traceback
            print(f"[ERROR] Generation failed: {e}")
            print(f"[ERROR] Traceback: {traceback.format_exc()}")
            await update.message.reply_text(
                f"❌ Ошибка при генерации поздравления: {e}\n\n"
                f"Проверьте:\n"
                f"1. Правильность API ключей GigaChat в .env\n"
                f"2. Подключение к интернету\n"
                f"3. Попробуйте еще раз, используя команду /generate для просмотра формата"
            )
    
    def run(self):
        """Запуск бота"""
        print("🤖 Бот запущен! Нажмите Ctrl+C для остановки.")
        self.application.run_polling(allowed_updates=Update.ALL_TYPES)


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
    
    # Создаем и запускаем бота
    bot = GreetingBot(token)
    bot.run()


if __name__ == "__main__":
    main()
