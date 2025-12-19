"""
Модуль для работы с API GigaChat для генерации изображений и текстов
"""
from .gigachat_module import GigaChatAPI, generate_image_from_prompt, load_api_keys_from_env

from .prompt import (
    GigaChatPrompt,
    generate_greeting_image
)

from .text_generator import (
    GigaChatTextGenerator,
    generate_greeting_text
)

from .sincerity_evaluator import (
    SincerityEvaluator,
    evaluate_sincerity,
    is_text_sincere_enough
)

__all__ = [
    'GigaChatAPI',
    'generate_image_from_prompt',
    'load_api_keys_from_env',
    'GigaChatPrompt',
    'generate_greeting_image',
    'GigaChatTextGenerator',
    'generate_greeting_text',
    'SincerityEvaluator',
    'evaluate_sincerity',
    'is_text_sincere_enough'
]

# Импортируем официальную библиотеку gigachat
try:
    import gigachat
    from gigachat import GigaChat
except ImportError:
    gigachat = None
    GigaChat = None

