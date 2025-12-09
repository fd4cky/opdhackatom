"""
Модуль для формирования промптов и генерации поздравительных изображений через GigaChat API
Простой интерфейс: передай данные клиента и события - получи изображение
"""
from typing import Optional, Dict, List
from datetime import datetime
from .gigachat_module import GigaChatAPI, load_api_keys_from_env


def _detect_event_type_from_date(event_date: str) -> Optional[str]:
    """
    Определяет тип события на основе даты (государственные и профессиональные праздники РФ)
    
    Args:
        event_date: Дата в формате DD.MM.YYYY
    
    Returns:
        Тип события или None, если дата не совпадает с известными праздниками
    """
    try:
        day, month, _ = event_date.split(".")
        
        # Государственные праздники Российской Федерации
        if day == "01" and month == "01":
            return "новый_год"
        elif day == "07" and month == "01":
            return "рождество"
        elif day == "23" and month == "02":
            return "день_защитника_отечества"
        elif day == "08" and month == "03":
            return "8_марта"
        elif day == "01" and month == "05":
            return "день_весны_и_труда"
        elif day == "09" and month == "05":
            return "день_победы"
        elif day == "12" and month == "06":
            return "день_россии"
        elif day == "04" and month == "11":
            return "день_народного_единства"
        
        # Профессиональные праздники (основные)
        elif day == "08" and month == "09":
            return "день_финансиста"
        elif day == "02" and month == "12":
            return "день_банковского_работника"
        elif day == "21" and month == "11":
            return "день_бухгалтера"
        elif day == "30" and month == "06":
            return "день_экономиста"
        elif day == "26" and month == "05":
            return "день_предпринимателя"
        
        # Для остальных дат НЕ определяем автоматически - тип события должен быть указан явно
        return None
    except (ValueError, AttributeError):
        return None


class GigaChatPrompt:
    """Класс для генерации поздравительных изображений"""
    
    def __init__(
        self,
        credentials: Optional[str] = None,
        api_key: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None
    ):
        """Инициализация (ключи загружаются из .env если не указаны)"""
        # Если ключи не переданы, загружаем из .env
        if not credentials and not api_key and (not client_id or not client_secret):
            env_credentials, env_api_key, env_client_id, env_client_secret = load_api_keys_from_env()
            credentials = credentials or env_credentials or env_api_key
            api_key = api_key or env_api_key
            client_id = client_id or env_client_id
            client_secret = client_secret or env_client_secret
        
        self.api = GigaChatAPI(
            credentials=credentials,
            api_key=api_key,
            client_id=client_id,
            client_secret=client_secret
        )
    
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
        
        # Если event_type не указан, пробуем определить только для известных фиксированных праздников
        if not event_type:
            event_type = _detect_event_type_from_date(event_date)
            # Если не удалось определить автоматически, требуем явного указания
            if not event_type:
                raise ValueError(
                    f"Тип события не указан и не может быть определен автоматически по дате {event_date}. "
                    f"Пожалуйста, укажите тип события явно в свободной форме."
                )
        
        # Элементы для известных событий (на русском для GigaChat)
        # Если тип события не в списке, используем общие праздничные элементы
        event_elements = {
            # Государственные праздники РФ
            "новый_год": "новогодняя елка, снежинки, фейерверки, шампанское, праздничная атмосфера",
            "рождество": "рождественская елка, звезда, свечи, зимняя атмосфера, праздничное настроение",
            "день_защитника_отечества": "военная символика, георгиевская лента, защита, патриотизм, российский флаг",
            "8_марта": "весенние цветы, тюльпаны, мимоза, весенняя атмосфера, женская элегантность",
            "день_весны_и_труда": "весенние цветы, солнце, труд, достижения, праздничная атмосфера",
            "день_победы": "георгиевская лента, гвоздики, военная символика, память, победа, российский флаг",
            "день_россии": "российский флаг, триколор, патриотизм, единство, гордость",
            "день_народного_единства": "российский флаг, единство, сплоченность, патриотизм, народ",
            
            # Профессиональные праздники
            "день_финансиста": "финансы, деньги, расчеты, бизнес успех, профессиональная атмосфера, корпоративный стиль",
            "день_банковского_работника": "банк, финансы, деньги, надежность, профессионализм, корпоративный стиль",
            "день_бухгалтера": "документы, расчеты, точность, профессионализм, корпоративный стиль",
            "день_экономиста": "экономика, графики, рост, профессионализм, корпоративный стиль",
            "день_предпринимателя": "бизнес, успех, рост, достижения, корпоративный стиль",
            
            # Общие праздники
            "день_рождения": "праздничный торт, свечи, воздушные шары, подарки, праздничная атмосфера",
            "профессиональный_праздник": "бизнес успех, достижения, профессиональная атмосфера, корпоративный стиль",
            "юбилей": "празднование, достижения, важная веха, корпоративное торжество",
            "день_компании": "корпоративный стиль, бизнес успех, команда, рост"
        }
        
        # Нормализуем event_type для поиска (приводим к нижнему регистру и убираем пробелы)
        event_type_normalized = event_type.lower().replace(" ", "_") if event_type else None
        
        # Стили для разных тонов (на русском для GigaChat)
        tone_styles = {
            "официальный": "профессиональный корпоративный дизайн, элегантный, утонченный, деловой, корпоративный синий, золотой, белый",
            "дружеский": "теплый дружеский дизайн, приветливый, доступный, современный дизайн, теплые цвета, дружелюбные тона",
            "креативный": "креативный художественный дизайн, оригинальный, инновационный, художественный, яркие цвета, смелые акценты"
        }
        
        # Особенности для сегментов (на русском для GigaChat)
        segment_features = {
            "VIP": "премиум качество, эксклюзивный дизайн, элементы роскоши, ультра высокое качество",
            "новый": "приветливый, дружелюбный, установление связи, высокое качество",
            "лояльный": "благодарность, долгосрочное партнерство, ценность, персонализированный, высокое качество",
            "стандартный": "профессиональный, дружелюбный, высокое качество"
        }
        
        # Формируем упрощенный промпт для GigaChat
        # GigaChat лучше работает с короткими и простыми промптами
        prompt_parts = []
        
        # Основные элементы события (самое важное)
        # Пробуем найти в словаре по нормализованному ключу
        if event_type_normalized and event_type_normalized in event_elements:
            prompt_parts.append(event_elements[event_type_normalized])
        elif event_type:
            # Если тип события не в словаре, используем его как есть в промпте
            prompt_parts.append(f"праздник: {event_type}, праздничная атмосфера")
        
        # Стиль (упрощенный)
        if tone == "официальный":
            prompt_parts.append("корпоративный стиль, элегантный")
        elif tone == "дружеский":
            prompt_parts.append("теплый, дружелюбный")
        elif tone == "креативный":
            prompt_parts.append("креативный, яркий")
        
        # Сегмент (только ключевые слова)
        if client_segment == "VIP":
            prompt_parts.append("премиум, роскошь")
        elif client_segment == "новый":
            prompt_parts.append("приветливый")
        elif client_segment == "лояльный":
            prompt_parts.append("благодарность")
        
        # Компания (только название, без лишних слов)
        if company_name:
            # Убираем кавычки и лишние символы
            clean_company = company_name.replace("'", "").replace('"', '').replace("ООО", "").strip()
            if clean_company:
                prompt_parts.append(f"компания {clean_company}")
        
        # Объединяем в короткий промпт
        prompt = ", ".join(prompt_parts)
        
        # Если промпт получился слишком длинным, обрезаем до первых 3-4 элементов
        if len(prompt_parts) > 4:
            prompt = ", ".join(prompt_parts[:4])
        
        # ВАЖНО: Добавляем строгое указание, что на изображении НЕ ДОЛЖНО быть текста
        # Это критическое требование - только визуальные элементы, никакого текста
        prompt = f"ВАЖНО: НЕ ДОБАВЛЯЙ ТЕКСТ НА ИЗОБРАЖЕНИЕ. {prompt}, только визуальные элементы, БЕЗ ТЕКСТА, БЕЗ НАДПИСЕЙ, БЕЗ СЛОВ, БЕЗ БУКВ, БЕЗ ЦИФР, БЕЗ ПОДПИСЕЙ, БЕЗ ЛОГОТИПОВ С ТЕКСТОМ"
        
        # Генерируем изображение с усиленным негативным промптом, исключающим текст
        return self.api.generate_and_save(
            prompt=prompt,
            output_path=output_path,
            width=1024,
            height=1024,
            negative_prompt="текст, надписи, слова, буквы, цифры, подписи, логотипы с текстом, любой текст, любые надписи, любые слова, любые буквы, любые цифры, текст на изображении, надписи на изображении"
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
    credentials: Optional[str] = None,
    api_key: Optional[str] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None
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
        credentials: Ключ авторизации (опционально)
        api_key: API ключ (опционально)
        client_id: Client ID (опционально)
        client_secret: Client Secret (опционально)
    
    Returns:
        Путь к сохраненному изображению
    """
    prompt_gen = GigaChatPrompt(credentials, api_key, client_id, client_secret)
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
