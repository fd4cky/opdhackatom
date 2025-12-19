"""
Модуль для генерации текста поздравительных сообщений через GigaChat API
Использует те же данные, что и для генерации изображений
"""
from typing import Optional, Dict, List, Tuple
from datetime import datetime
import re
import asyncio
import time
from .gigachat_module import GigaChatAPI, load_api_keys_from_env
from .sincerity_evaluator import SincerityEvaluator


def _is_rate_limit_error(error: Exception) -> bool:
    """Проверяет, является ли ошибка ошибкой rate limit (429)"""
    error_str = str(error).lower()
    if '429' in error_str or 'too many requests' in error_str:
        return True
    
    # Проверяем, если ошибка - это кортеж с HTTP статусом
    if isinstance(error, tuple) and len(error) >= 2:
        if error[1] == 429:
            return True
    
    return False


def _get_retry_delay(attempt: int, base_delay: float = 5.0, max_delay: float = 120.0) -> float:
    """Вычисляет задержку для повторной попытки (экспоненциальная задержка)"""
    delay = base_delay * (2 ** attempt)
    return min(delay, max_delay)


def markdown_to_telegram_html(text: str) -> str:
    """
    Конвертирует Markdown разметку в HTML формат для Telegram
    
    Args:
        text: Текст с Markdown разметкой
    
    Returns:
        Текст с HTML разметкой для Telegram
    """
    if not text:
        return text
    
    # Экранируем HTML спецсимволы в исходном тексте
    # Но делаем это аккуратно, чтобы не экранировать то, что мы добавим
    def escape_html_safe(s: str) -> str:
        """Экранирует HTML символы, но не трогает уже существующие теги"""
        # Разбиваем на части: существующие HTML теги и обычный текст
        parts = re.split(r'(<[^>]+>)', s)
        result = []
        for part in parts:
            if part.startswith('<') and part.endswith('>'):
                # Это уже HTML тег, оставляем как есть
                result.append(part)
            else:
                # Это обычный текст, экранируем
                escaped = part.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
                result.append(escaped)
        return ''.join(result)
    
    # Сначала экранируем существующие HTML символы (кроме уже существующих тегов)
    text = escape_html_safe(text)
    
    # Обрабатываем Markdown разметку и конвертируем в HTML теги
    
    # Ссылки: [текст](URL) -> <a href="URL">текст</a>
    text = re.sub(r'\[([^\]]+?)\]\(([^\)]+?)\)', r'<a href="\2">\1</a>', text)
    
    # Жирный текст: **текст** или __текст__ -> <b>текст</b>
    text = re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', text)
    text = re.sub(r'__(.+?)__', r'<b>\1</b>', text)
    
    # Курсив: *текст* или _текст_ (только одиночные, не двойные) -> <i>текст</i>
    # Обрабатываем после жирного, чтобы не конфликтовать
    text = re.sub(r'(?<!\*)\*([^*\n]+?)\*(?!\*)', r'<i>\1</i>', text)
    text = re.sub(r'(?<!_)_([^_\n]+?)_(?!_)', r'<i>\1</i>', text)
    
    # Моноширинный текст: `текст` -> <code>текст</code>
    text = re.sub(r'`([^`]+?)`', r'<code>\1</code>', text)
    
    # Зачеркнутый текст: ~~текст~~ -> <s>текст</s>
    text = re.sub(r'~~(.+?)~~', r'<s>\1</s>', text)
    
    return text


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
            
            # Приоритет: API_KEY/CREDENTIALS > client_id/client_secret
            # Если есть API_KEY или CREDENTIALS, используем их и игнорируем client_id/client_secret
            if env_credentials or env_api_key:
                credentials = credentials or env_credentials or env_api_key
                api_key = api_key or env_api_key
                # Не используем client_id/client_secret, если есть API_KEY
                client_id = None
                client_secret = None
            else:
                # Используем client_id/client_secret только если нет API_KEY
                client_id = client_id or env_client_id
                client_secret = client_secret or env_client_secret
        
        # Сохраняем ключи для передачи в SincerityEvaluator
        self.credentials = credentials
        self.api_key = api_key
        self.client_id = client_id
        self.client_secret = client_secret
        
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
        interaction_history: Optional[Dict] = None,
        evaluate_sincerity: bool = False,
        min_sincerity: float = 0.6,
        max_retries: int = 2
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
            evaluate_sincerity: Если True, оценивает искренность текста и перегенерирует при низкой оценке
            min_sincerity: Минимальный порог искренности (0.0-1.0) для перегенерации
            max_retries: Максимальное количество попыток перегенерации при низкой искренности
        
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
            f"- Длина: 3-5 предложений\n"
            f"- В конце сообщения должна быть подпись: \"С уважением,\\nСбер\"\n"
            f"- НЕ используй конструкции типа \"от имени сотрудников и руководства\" или подобные\n"
            f"- Подпись должна быть только в формате: \"С уважением,\\nСбер\"\n\n"
            f"Напиши полный текст поздравления с подписью в конце."
        )
        
        # Генерируем текст через GigaChat API с возможной перегенерацией при низкой искренности
        best_text = None
        best_scores = None
        
        # Отдельный счетчик для обработки ошибки 429
        rate_limit_retries = 0
        max_rate_limit_retries = 5  # Больше попыток для ошибки 429
        
        for attempt in range(max_retries + 1):
            try:
                # Используем chat API для генерации текста (без function_call)
                chat_payload = {
                    "messages": [
                        {"role": "user", "content": prompt}
                    ]
                }
                
                response = self.api.client.chat(chat_payload)
                # Сбрасываем счетчик ошибок 429 при успешном запросе
                rate_limit_retries = 0
                
                # Извлекаем текст из ответа
                if hasattr(response, 'choices') and len(response.choices) > 0:
                    message = response.choices[0].message
                    content = message.content if hasattr(message, 'content') else str(message)
                    
                    if isinstance(content, str) and content.strip():
                        greeting_text = content.strip()
                        
                        # Убираем возможные дублирующиеся подписи
                        # Если есть "от имени сотрудников и руководства", удаляем эту часть
                        # Удаляем конструкции типа "от имени сотрудников и руководства [название банка]"
                        greeting_text = re.sub(
                            r'С уважением,\s*от имени сотрудников и руководства[^.]*\.',
                            '',
                            greeting_text,
                            flags=re.IGNORECASE
                        )
                        greeting_text = re.sub(
                            r'от имени сотрудников и руководства[^.]*\.',
                            '',
                            greeting_text,
                            flags=re.IGNORECASE
                        )
                        
                        # Проверяем, есть ли уже подпись "С уважением, Сбер"
                        if "С уважением" in greeting_text and "Сбер" in greeting_text:
                            # Если есть, оставляем как есть
                            pass
                        else:
                            # Если нет правильной подписи, добавляем
                            greeting_text = greeting_text.rstrip()
                            if not greeting_text.endswith("Сбер"):
                                greeting_text += "\n\nС уважением,\nСбер"
                        
                        # Если включена оценка искренности, проверяем текст
                        if evaluate_sincerity:
                            # Создаем контекст для оценки
                            eval_context = {
                                "event_type": event_type,
                                "client_segment": client_segment,
                                "tone": tone
                            }
                            
                            # Оцениваем искренность (используем текст до конвертации в HTML)
                            evaluator = SincerityEvaluator(
                                credentials=self.credentials,
                                api_key=self.api_key,
                                client_id=self.client_id,
                                client_secret=self.client_secret
                            )
                            
                            # Убираем HTML теги для оценки (если они уже есть)
                            text_for_eval = re.sub(r'<[^>]+>', '', greeting_text)
                            scores = evaluator.evaluate(text_for_eval, eval_context)
                            
                            # Логируем оценку
                            print(f"[INFO] Попытка {attempt + 1}: Оценка искренности = {scores['sincerity_score']:.2f}")
                            
                            # Сохраняем лучший вариант
                            if best_text is None or scores['sincerity_score'] > (best_scores['sincerity_score'] if best_scores else 0):
                                best_text = greeting_text
                                best_scores = scores
                            
                            # Проверяем, достаточно ли искренен текст
                            is_sincere, _ = evaluator.is_sincere_enough(text_for_eval, min_sincerity, eval_context)
                            
                            if is_sincere or attempt >= max_retries:
                                # Текст достаточно искренен или достигли максимума попыток
                                greeting_text = best_text
                                break
                            else:
                                # Текст недостаточно искренен, пробуем перегенерировать
                                if attempt < max_retries:
                                    print(f"[INFO] Текст недостаточно искренен ({scores['sincerity_score']:.2f} < {min_sincerity}), перегенерирую...")
                                    # Усиливаем промпт для большей искренности
                                    prompt = (
                                        f"Напиши ИСКРЕННЕЕ и БОЛЕЕ ПЕРСОНАЛИЗИРОВАННОЕ поздравительное сообщение для клиента банка по случаю {event_name}.\n\n"
                                        f"Контекст:\n{context}\n\n"
                                        f"Требования:\n"
                                        f"- Тон: {tone}\n"
                                        f"- Обращение должно быть МАКСИМАЛЬНО персонализированным и искренним\n"
                                        f"- Избегай шаблонных фраз, используй более личный подход\n"
                                        f"- Упоминание компании клиента, если указано\n"
                                        f"- Упоминание важности партнерства\n"
                                        f"- Пожелания успехов и процветания\n"
                                        f"- Длина: 3-5 предложений\n"
                                        f"- В конце сообщения должна быть подпись: \"С уважением,\\nСбер\"\n"
                                        f"- НЕ используй конструкции типа \"от имени сотрудников и руководства\" или подобные\n"
                                        f"- Подпись должна быть только в формате: \"С уважением,\\nСбер\"\n\n"
                                        f"Напиши полный текст поздравления с подписью в конце. Текст должен звучать искренне и тепло."
                                    )
                                    continue
                        else:
                            # Оценка искренности не включена, возвращаем текст
                            # Конвертируем Markdown в HTML для Telegram
                            greeting_text = markdown_to_telegram_html(greeting_text)
                            return greeting_text.strip()
                    else:
                        raise Exception("GigaChat вернул пустой ответ")
                else:
                    raise Exception(f"Неожиданный формат ответа от GigaChat API: {response}")
                    
            except Exception as e:
                # Проверяем, является ли это ошибкой rate limit (429)
                if _is_rate_limit_error(e):
                    rate_limit_retries += 1
                    if rate_limit_retries > max_rate_limit_retries:
                        raise Exception(
                            f"Ошибка 429 (Too Many Requests) при генерации текста после {max_rate_limit_retries} попыток.\n"
                            f"Возможно, исчерпана квота токенов или превышен rate limit.\n"
                            f"Попробуйте позже или проверьте квоту API."
                        )
                    
                    delay = _get_retry_delay(rate_limit_retries - 1)  # Используем отдельный счетчик для задержки
                    print(f"[WARNING] Ошибка 429 (Too Many Requests) при попытке {rate_limit_retries}/{max_rate_limit_retries}: {e}")
                    print(f"[INFO] Ожидание {delay:.1f} секунд перед повторной попыткой...")
                    time.sleep(delay)
                    # Продолжаем цикл, не увеличивая attempt
                    continue
                
                # Для других ошибок проверяем обычный лимит попыток
                if attempt >= max_retries:
                    raise Exception(f"Ошибка генерации текста через GigaChat: {e}")
                
                print(f"[WARNING] Ошибка при попытке {attempt + 1}: {e}, пробую еще раз...")
                # Небольшая задержка для других ошибок
                time.sleep(1.0)
                
                continue
        
        # Если дошли сюда, возвращаем лучший вариант (или последний, если оценка не включена)
        if best_text:
            # Конвертируем Markdown в HTML для Telegram
            final_text = markdown_to_telegram_html(best_text)
            if best_scores:
                print(f"[INFO] Финальная оценка искренности: {best_scores['sincerity_score']:.2f}")
            return final_text.strip()
        else:
            raise Exception("Не удалось сгенерировать текст после всех попыток")


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
    evaluate_sincerity: bool = False,
    min_sincerity: float = 0.6,
    max_retries: int = 2,
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
        evaluate_sincerity: Если True, оценивает искренность текста и перегенерирует при низкой оценке
        min_sincerity: Минимальный порог искренности (0.0-1.0) для перегенерации
        max_retries: Максимальное количество попыток перегенерации при низкой искренности
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
        interaction_history=interaction_history,
        evaluate_sincerity=evaluate_sincerity,
        min_sincerity=min_sincerity,
        max_retries=max_retries
    )

