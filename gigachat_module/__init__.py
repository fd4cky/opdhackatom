"""
Модуль для работы с API GigaChat для генерации изображений
"""
from .gigachat_module import GigaChatAPI, generate_image_from_prompt, load_api_keys_from_env

from .prompt import (
    GigaChatPrompt,
    generate_greeting_image
)

__all__ = [
    'GigaChatAPI',
    'generate_image_from_prompt',
    'load_api_keys_from_env',
    'GigaChatPrompt',
    'generate_greeting_image'
]

# Импортируем официальную библиотеку gigachat
try:
    import gigachat
    from gigachat import GigaChat
except ImportError:
    gigachat = None
    GigaChat = None

