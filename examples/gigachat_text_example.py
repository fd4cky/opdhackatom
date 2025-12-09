"""
Пример генерации поздравительного текста через GigaChat API

Демонстрирует:
- Как передать данные клиента и события
- Как сгенерировать персонализированный текст поздравления
- Как получить готовый текст через GigaChat

Запуск: python examples/gigachat_text_example.py
"""
import sys
import os

# Добавляем корневую директорию проекта в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from gigachat_module.text_generator import generate_greeting_text


def main():
    """Пример генерации поздравительного текста для клиента через GigaChat"""
    
    # Данные клиента и события
    client_data = {
        "event_date": "01.01.2025",  # Дата события (обязательно) - тип события определится автоматически
        "client_name": "Иван Петров",  # Имя клиента
        "company_name": "ООО 'ТехноСтрой'",  # Название компании
        "position": "Генеральный директор",  # Должность
        "client_segment": "VIP",  # Сегмент клиента (VIP, новый, лояльный, стандартный)
        "tone": "официальный",  # Тон (официальный, дружеский, креативный)
        "preferences": ["премиум качество", "корпоративный стиль"],  # Предпочтения
        "interaction_history": {  # История взаимодействий
            "last_contact": "2024-12-15",
            "topic": "кредитная линия"
        }
    }
    
    print("Генерация поздравительного текста через GigaChat...")
    print(f"Клиент: {client_data['client_name']}")
    print(f"Компания: {client_data['company_name']}")
    print(f"Дата события: {client_data['event_date']}")
    print(f"Сегмент: {client_data['client_segment']}, Тон: {client_data['tone']}")
    print()
    
    try:
        # Генерируем текст - просто передаем данные и получаем результат
        greeting_text = generate_greeting_text(
            event_date=client_data["event_date"],
            event_type=client_data.get("event_type"),  # Опционально - определится по дате
            client_name=client_data["client_name"],
            company_name=client_data["company_name"],
            position=client_data["position"],
            client_segment=client_data["client_segment"],
            tone=client_data["tone"],
            preferences=client_data["preferences"],
            interaction_history=client_data["interaction_history"]
        )
        
        print("✓ Текст поздравления успешно сгенерирован:")
        print()
        print("-" * 60)
        print(greeting_text)
        print("-" * 60)
        
    except Exception as e:
        print(f"✗ Ошибка: {e}")
        print("\nПроверьте:")
        print("1. Установлены ли переменные окружения GIGACHAT_CREDENTIALS или GIGACHAT_API_KEY")
        print("2. Правильность API ключей в файле .env")
        print("3. Наличие сертификата russian_trusted_root_ca_pem.crt в папке gigachat_module/")


if __name__ == "__main__":
    main()

