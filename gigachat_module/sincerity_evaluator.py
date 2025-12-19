"""
Модуль для оценки искренности генерируемых поздравительных текстов
Использует GigaChat API для анализа текста на искренность
"""
from typing import Dict, Optional, Tuple
import time
from .gigachat_module import GigaChatAPI, load_api_keys_from_env


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


class SincerityEvaluator:
    """Класс для оценки искренности поздравительных текстов"""
    
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
        
        self.api = GigaChatAPI(
            credentials=credentials,
            api_key=api_key,
            client_id=client_id,
            client_secret=client_secret
        )
    
    def evaluate(
        self,
        text: str,
        context: Optional[Dict] = None
    ) -> Dict[str, float]:
        """
        Оценивает искренность поздравительного текста
        
        Args:
            text: Текст поздравления для оценки
            context: Дополнительный контекст (event_type, client_segment, tone и т.д.)
        
        Returns:
            Словарь с оценками:
            {
                "sincerity_score": float (0.0-1.0),  # Общая оценка искренности
                "warmth_score": float (0.0-1.0),     # Оценка теплоты
                "personalization_score": float (0.0-1.0),  # Оценка персонализации
                "authenticity_score": float (0.0-1.0)  # Оценка аутентичности
            }
        """
        if not text or not text.strip():
            return {
                "sincerity_score": 0.0,
                "warmth_score": 0.0,
                "personalization_score": 0.0,
                "authenticity_score": 0.0
            }
        
        # Формируем промпт для оценки искренности
        context_info = ""
        if context:
            context_parts = []
            if context.get("event_type"):
                context_parts.append(f"Тип события: {context['event_type']}")
            if context.get("client_segment"):
                context_parts.append(f"Сегмент клиента: {context['client_segment']}")
            if context.get("tone"):
                context_parts.append(f"Требуемый тон: {context['tone']}")
            if context_parts:
                context_info = "\n".join(context_parts) + "\n\n"
        
        prompt = (
            f"Оцени искренность следующего поздравительного текста для клиента банка.\n\n"
            f"{context_info}"
            f"Текст для оценки:\n{text}\n\n"
            f"Оцени текст по следующим критериям (от 0.0 до 1.0):\n"
            f"1. Искренность (sincerity_score) - насколько текст звучит искренне, а не шаблонно\n"
            f"2. Теплота (warmth_score) - насколько текст теплый и дружелюбный\n"
            f"3. Персонализация (personalization_score) - насколько текст персонализирован под конкретного клиента\n"
            f"4. Аутентичность (authenticity_score) - насколько текст звучит естественно и аутентично\n\n"
            f"Ответь ТОЛЬКО в формате JSON без дополнительных комментариев:\n"
            f'{{\n'
            f'  "sincerity_score": <число от 0.0 до 1.0>,\n'
            f'  "warmth_score": <число от 0.0 до 1.0>,\n'
            f'  "personalization_score": <число от 0.0 до 1.0>,\n'
            f'  "authenticity_score": <число от 0.0 до 1.0>\n'
            f'}}'
        )
        
        max_retries = 5  # Увеличено количество попыток для ошибки 429
        for attempt in range(max_retries + 1):
            try:
                # Используем chat API для оценки
                chat_payload = {
                    "messages": [
                        {"role": "user", "content": prompt}
                    ]
                }
                
                response = self.api.client.chat(chat_payload)
                
                # Извлекаем ответ
                if hasattr(response, 'choices') and len(response.choices) > 0:
                    message = response.choices[0].message
                    content = message.content if hasattr(message, 'content') else str(message)
                    
                    if isinstance(content, str) and content.strip():
                        # Парсим JSON из ответа
                        import json
                        import re
                        
                        # Извлекаем JSON из ответа (может быть обернут в markdown код)
                        json_match = re.search(r'\{[^{}]*"sincerity_score"[^{}]*\}', content, re.DOTALL)
                        if json_match:
                            json_str = json_match.group(0)
                        else:
                            # Пробуем найти JSON в кодовых блоках
                            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content, re.DOTALL)
                            if json_match:
                                json_str = json_match.group(1)
                            else:
                                json_str = content.strip()
                        
                        # Парсим JSON
                        try:
                            result = json.loads(json_str)
                            
                            # Валидируем и нормализуем значения
                            scores = {
                                "sincerity_score": self._normalize_score(result.get("sincerity_score", 0.5)),
                                "warmth_score": self._normalize_score(result.get("warmth_score", 0.5)),
                                "personalization_score": self._normalize_score(result.get("personalization_score", 0.5)),
                                "authenticity_score": self._normalize_score(result.get("authenticity_score", 0.5))
                            }
                            
                            return scores
                        except json.JSONDecodeError as e:
                            # Если не удалось распарсить JSON, возвращаем средние значения
                            print(f"[WARNING] Не удалось распарсить JSON ответ от GigaChat: {e}")
                            print(f"[WARNING] Ответ был: {content[:200]}")
                            return self._default_scores()
                    else:
                        if attempt >= max_retries:
                            return self._default_scores()
                        continue
                else:
                    if attempt >= max_retries:
                        return self._default_scores()
                    continue
                
            except Exception as e:
                if attempt >= max_retries:
                    print(f"[ERROR] Ошибка оценки искренности через GigaChat после {max_retries + 1} попыток: {e}")
                    return self._default_scores()
                
                # Проверяем, является ли это ошибкой rate limit (429)
                if _is_rate_limit_error(e):
                    delay = _get_retry_delay(attempt)
                    print(f"[WARNING] Ошибка 429 (Too Many Requests) при оценке искренности, попытка {attempt + 1}: {e}")
                    print(f"[INFO] Ожидание {delay:.1f} секунд перед повторной попыткой...")
                    time.sleep(delay)
                else:
                    print(f"[WARNING] Ошибка при оценке искренности, попытка {attempt + 1}: {e}")
                    time.sleep(1.0)
                
                continue
        
        # Если дошли сюда, значит не удалось получить ответ
        return self._default_scores()
    
    def _normalize_score(self, score) -> float:
        """Нормализует оценку в диапазон 0.0-1.0"""
        try:
            score_float = float(score)
            # Ограничиваем диапазон
            if score_float < 0.0:
                return 0.0
            elif score_float > 1.0:
                return 1.0
            return score_float
        except (ValueError, TypeError):
            return 0.5  # Среднее значение по умолчанию
    
    def _default_scores(self) -> Dict[str, float]:
        """Возвращает оценки по умолчанию (средние)"""
        return {
            "sincerity_score": 0.5,
            "warmth_score": 0.5,
            "personalization_score": 0.5,
            "authenticity_score": 0.5
        }
    
    def is_sincere_enough(
        self,
        text: str,
        min_sincerity: float = 0.6,
        context: Optional[Dict] = None
    ) -> Tuple[bool, Dict[str, float]]:
        """
        Проверяет, достаточно ли искренен текст
        
        Args:
            text: Текст для проверки
            min_sincerity: Минимальный порог искренности (по умолчанию 0.6)
            context: Дополнительный контекст
        
        Returns:
            Кортеж (is_sincere, scores):
            - is_sincere: True если текст достаточно искренен
            - scores: Словарь с оценками
        """
        scores = self.evaluate(text, context)
        overall_sincerity = scores["sincerity_score"]
        
        # Можно использовать взвешенную оценку
        # Например, учитывать все метрики, но с акцентом на sincerity_score
        weighted_score = (
            scores["sincerity_score"] * 0.4 +
            scores["warmth_score"] * 0.2 +
            scores["personalization_score"] * 0.2 +
            scores["authenticity_score"] * 0.2
        )
        
        is_sincere = weighted_score >= min_sincerity
        
        return is_sincere, scores


def evaluate_sincerity(
    text: str,
    context: Optional[Dict] = None,
    credentials: Optional[str] = None,
    api_key: Optional[str] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None
) -> Dict[str, float]:
    """
    Простая функция для оценки искренности текста
    
    Args:
        text: Текст поздравления для оценки
        context: Дополнительный контекст (event_type, client_segment, tone и т.д.)
        credentials: Ключ авторизации (опционально)
        api_key: API ключ (опционально)
        client_id: Client ID (опционально)
        client_secret: Client Secret (опционально)
    
    Returns:
        Словарь с оценками искренности
    """
    evaluator = SincerityEvaluator(credentials, api_key, client_id, client_secret)
    return evaluator.evaluate(text, context)


def is_text_sincere_enough(
    text: str,
    min_sincerity: float = 0.6,
    context: Optional[Dict] = None,
    credentials: Optional[str] = None,
    api_key: Optional[str] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None
) -> Tuple[bool, Dict[str, float]]:
    """
    Проверяет, достаточно ли искренен текст
    
    Args:
        text: Текст для проверки
        min_sincerity: Минимальный порог искренности (по умолчанию 0.6)
        context: Дополнительный контекст
        credentials: Ключ авторизации (опционально)
        api_key: API ключ (опционально)
        client_id: Client ID (опционально)
        client_secret: Client Secret (опционально)
    
    Returns:
        Кортеж (is_sincere, scores)
    """
    evaluator = SincerityEvaluator(credentials, api_key, client_id, client_secret)
    return evaluator.is_sincere_enough(text, min_sincerity, context)

