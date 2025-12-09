"""
Модуль для генерации текста поздравительных сообщений через GigaChat API
Использует те же данные, что и для генерации изображений
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


class GigaChatTextGenerator:
    """Класс для генерации поздравительных текстов"""
    
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
        Генерирует поздравительный текст
        
        Args:
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
            Текст поздравления
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
        
        # Формируем промпт для генерации текста
        prompt_parts = []
        
        # Основная информация о событии
        # Если тип события указан, используем его как есть (в свободной форме)
        # Для известных праздников можно использовать более красивые названия
        event_names = {
            # Государственные праздники РФ
            "новый_год": "Новый год",
            "рождество": "Рождество Христово",
            "день_защитника_отечества": "День защитника Отечества",
            "8_марта": "Международный женский день (8 Марта)",
            "день_весны_и_труда": "Праздник Весны и Труда",
            "день_победы": "День Победы",
            "день_россии": "День России",
            "день_народного_единства": "День народного единства",
            
            # Профессиональные праздники
            "день_финансиста": "День финансиста",
            "день_банковского_работника": "День банковского работника",
            "день_бухгалтера": "День бухгалтера",
            "день_экономиста": "День экономиста",
            "день_предпринимателя": "День предпринимателя",
            
            # Общие праздники
            "день_рождения": "день рождения",
            "профессиональный_праздник": "профессиональный праздник",
            "юбилей": "юбилей",
            "день_компании": "день компании"
        }
        
        # Нормализуем event_type для поиска
        event_type_normalized = event_type.lower().replace(" ", "_") if event_type else None
        event_name = event_names.get(event_type_normalized, event_type) if event_type else "праздник"
        
        # Формируем контекст для промпта
        context_parts = []
        
        # Обращение
        if client_name:
            context_parts.append(f"Клиент: {client_name}")
        
        if company_name:
            context_parts.append(f"Компания: {company_name}")
        
        if position:
            context_parts.append(f"Должность: {position}")
        
        # Сегмент и тон
        segment_info = {
            "VIP": "VIP-клиент, требует премиум подхода",
            "новый": "новый клиент, важно произвести хорошее впечатление",
            "лояльный": "лояльный клиент, долгосрочное партнерство",
            "стандартный": "стандартный клиент"
        }
        
        if client_segment in segment_info:
            context_parts.append(segment_info[client_segment])
        
        tone_info = {
            "официальный": "официальный, уважительный тон",
            "дружеский": "теплый, дружеский тон",
            "креативный": "креативный, оригинальный подход"
        }
        
        if tone in tone_info:
            context_parts.append(tone_info[tone])
        
        # История взаимодействий
        if interaction_history and interaction_history.get("topic"):
            context_parts.append(f"Тема последнего взаимодействия: {interaction_history['topic']}")
        
        # Предпочтения
        if preferences:
            context_parts.append(f"Предпочтения: {', '.join(preferences)}")
        
        # Формируем финальный промпт
        context = "\n".join(context_parts) if context_parts else "стандартный клиент"
        
        prompt = (
            f"Напиши поздравительное сообщение для клиента банка по случаю {event_name}.\n\n"
            f"Контекст:\n{context}\n\n"
            f"Требования:\n"
            f"- Тон: {tone}\n"
            f"- Обращение должно быть персонализированным\n"
            f"- Упоминание компании клиента, если указано\n"
            f"- Упоминание важности партнерства\n"
            f"- Пожелания успехов и процветания\n"
            f"- Длина: 3-5 предложений\n\n"
            f"Напиши только текст поздравления, без дополнительных комментариев."
        )
        
        # Генерируем текст через GigaChat API
        try:
            # Используем chat API для генерации текста (без function_call)
            chat_payload = {
                "messages": [
                    {"role": "user", "content": prompt}
                ]
            }
            
            response = self.api.client.chat(chat_payload)
            
            # Извлекаем текст из ответа
            if hasattr(response, 'choices') and len(response.choices) > 0:
                message = response.choices[0].message
                content = message.content if hasattr(message, 'content') else str(message)
                
                if isinstance(content, str) and content.strip():
                    return content.strip()
                else:
                    raise Exception("GigaChat вернул пустой ответ")
            else:
                raise Exception(f"Неожиданный формат ответа от GigaChat API: {response}")
                
        except Exception as e:
            raise Exception(f"Ошибка генерации текста через GigaChat: {e}")


def generate_greeting_text(
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
    Простая функция для генерации поздравительного текста
    
    Args:
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
        Текст поздравления
    """
    generator = GigaChatTextGenerator(credentials, api_key, client_id, client_secret)
    return generator.generate(
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

