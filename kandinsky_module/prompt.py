"""
Модуль для формирования промптов и генерации поздравительных изображений через Kandinsky API
Простой интерфейс: передай данные клиента и события - получи изображение
"""
from typing import Optional, Dict, List
from datetime import datetime
from .kandinsky_module import KandinskyAPI, load_api_keys_from_env


def _detect_event_type_from_date(event_date: str) -> str:
    """
    Определяет тип события на основе даты
    
    Args:
        event_date: Дата в формате DD.MM.YYYY
    
    Returns:
        Тип события (новый_год, 8_марта, день_рождения и т.д.)
    """
    try:
        day, month, _ = event_date.split(".")
        
        # Фиксированные праздники
        if day == "01" and month == "01":
            return "новый_год"
        elif day == "08" and month == "03":
            return "8_марта"
        
        # Для остальных дат по умолчанию день_рождения
        # Можно расширить логику для других праздников
        return "день_рождения"
    except (ValueError, AttributeError):
        # Если не удалось распарсить дату, возвращаем день_рождения
        return "день_рождения"


class KandinskyPrompt:
    """Класс для генерации поздравительных изображений"""
    
    def __init__(self, api_key: Optional[str] = None, secret_key: Optional[str] = None):
        """Инициализация (ключи загружаются из .env если не указаны)"""
        if api_key and secret_key:
            self.api = KandinskyAPI(api_key, secret_key)
        else:
            api_key, secret_key = load_api_keys_from_env()
            if not api_key or not secret_key:
                raise ValueError("Необходимо указать API ключи или создать .env файл")
            self.api = KandinskyAPI(api_key, secret_key)
    
    def generate(
        self,
        output_path: str,
        event_date: str,
        event_type: Optional[str] = None,
        client_name: Optional[str] = None,
        company_name: Optional[str] = None,
        position: Optional[str] = None,
        client_segment: str = "стандартный",
        tone: str = "официальный",
        preferences: Optional[List[str]] = None,
        interaction_history: Optional[Dict] = None
    ) -> str:
        """
        Генерирует поздравительное изображение
        
        Args:
            output_path: Путь для сохранения изображения
            event_date: Дата события (DD.MM.YYYY) - обязательный параметр
            event_type: Тип события (новый_год, день_рождения, 8_марта, профессиональный_праздник, юбилей).
                       Если не указан, определяется автоматически по дате
            client_name: Имя клиента
            company_name: Название компании
            position: Должность
            client_segment: Сегмент (VIP, новый, лояльный, стандартный)
            tone: Тон (официальный, дружеский, креативный)
            preferences: Предпочтения клиента
            interaction_history: История взаимодействий {"last_contact": "...", "topic": "..."}
        
        Returns:
            Путь к сохраненному изображению
        """
        # Валидируем формат даты
        try:
            datetime.strptime(event_date, "%d.%m.%Y")
        except ValueError:
            raise ValueError(f"Неверный формат даты: {event_date}. Ожидается формат DD.MM.YYYY")
        
        # Если event_type не указан, определяем его по дате
        if not event_type:
            event_type = _detect_event_type_from_date(event_date)
        # Элементы для разных событий
        event_elements = {
            "новый_год": "Christmas tree, snowflakes, fireworks, champagne, holiday atmosphere",
            "день_рождения": "birthday cake, candles, balloons, gifts, party atmosphere",
            "8_марта": "spring flowers, tulips, mimosa, spring atmosphere, feminine elegance",
            "профессиональный_праздник": "business success, achievements, professional atmosphere, corporate style",
            "юбилей": "celebration, achievements, milestone, corporate celebration",
            "день_компании": "corporate style, business success, team, growth"
        }
        
        # Стили для разных тонов
        tone_styles = {
            "официальный": "professional corporate design, elegant, sophisticated, business-like, corporate blue, gold, white",
            "дружеский": "warm friendly design, welcoming, approachable, modern design, warm colors, friendly tones",
            "креативный": "creative artistic design, original, innovative, artistic, vibrant colors, bold accents"
        }
        
        # Особенности для сегментов
        segment_features = {
            "VIP": "premium quality, exclusive design, luxury elements, ultra high quality",
            "новый": "welcoming, friendly, establishing connection, high quality",
            "лояльный": "appreciation, long-term partnership, value, personalized, high quality",
            "стандартный": "professional, friendly, high quality"
        }
        
        # Формируем промпт
        prompt_parts = []
        
        # Элементы события
        if event_type in event_elements:
            prompt_parts.append(event_elements[event_type])
        
        # Дата
        if event_date:
            prompt_parts.append(f"date: {event_date}")
        
        # Стиль и тон
        if tone in tone_styles:
            prompt_parts.append(tone_styles[tone])
        
        # Сегмент
        if client_segment in segment_features:
            prompt_parts.append(segment_features[client_segment])
        
        # Компания
        if company_name:
            prompt_parts.append(f"corporate style of {company_name}")
        
        # Должность (добавляем контекст)
        if position:
            if "директор" in position.lower() or "руководитель" in position.lower():
                prompt_parts.append("executive level, leadership")
            elif "финанс" in position.lower():
                prompt_parts.append("financial sector, business")
        
        # Предпочтения
        if preferences:
            prompt_parts.append(f"client preferences: {', '.join(preferences)}")
        
        # История взаимодействий
        if interaction_history and interaction_history.get("topic"):
            topic = interaction_history["topic"].lower()
            if "кредит" in topic or "займ" in topic:
                prompt_parts.append("financial services context")
            elif "расчет" in topic or "обслуживание" in topic:
                prompt_parts.append("banking services context")
        
        # Обязательные элементы
        prompt_parts.append("high quality greeting card, professional design, suitable for corporate use")
        
        # Объединяем в промпт
        prompt = ", ".join(prompt_parts)
        
        # Генерируем изображение
        return self.api.generate_and_save(
            prompt=prompt,
            output_path=output_path,
            width=1024,
            height=1024
        )


def generate_greeting_image(
    output_path: str,
    event_date: str,
    event_type: Optional[str] = None,
    client_name: Optional[str] = None,
    company_name: Optional[str] = None,
    position: Optional[str] = None,
    client_segment: str = "стандартный",
    tone: str = "официальный",
    preferences: Optional[List[str]] = None,
    interaction_history: Optional[Dict] = None,
    api_key: Optional[str] = None,
    secret_key: Optional[str] = None
) -> str:
    """
    Простая функция для генерации поздравительного изображения
    
    Args:
        output_path: Путь для сохранения
        event_date: Дата события (DD.MM.YYYY) - обязательный параметр
        event_type: Тип события (новый_год, день_рождения, 8_марта, профессиональный_праздник, юбилей).
                   Если не указан, определяется автоматически по дате
        client_name: Имя клиента
        company_name: Название компании
        position: Должность
        client_segment: Сегмент (VIP, новый, лояльный, стандартный)
        tone: Тон (официальный, дружеский, креативный)
        preferences: Предпочтения клиента
        interaction_history: История взаимодействий {"last_contact": "...", "topic": "..."}
        api_key: API ключ (опционально)
        secret_key: Secret ключ (опционально)
    
    Returns:
        Путь к сохраненному изображению
    """
    prompt_gen = KandinskyPrompt(api_key, secret_key)
    return prompt_gen.generate(
        output_path=output_path,
        event_date=event_date,
        event_type=event_type,
        client_name=client_name,
        company_name=company_name,
        position=position,
        client_segment=client_segment,
        tone=tone,
        preferences=preferences,
        interaction_history=interaction_history
    )
