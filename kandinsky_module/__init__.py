"""
Модуль для работы с API Kandinsky (Fusion Brain)
"""

from .kandinsky_module import (
    KandinskyAPI,
    generate_image_from_prompt,
    load_api_keys_from_env
)

from .prompt import (
    KandinskyPrompt,
    generate_greeting_image
)

__all__ = [
    'KandinskyAPI',
    'generate_image_from_prompt',
    'load_api_keys_from_env',
    'KandinskyPrompt',
    'generate_greeting_image'
]

