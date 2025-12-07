"""
Пример генерации поздравительного изображения через GigaChat API

Демонстрирует:
- Как передать данные клиента и события
- Как сформировать промпт автоматически
- Как получить готовое изображение через GigaChat

Запуск: python examples/gigachat_greeting_example.py
"""
import sys
import os

# Добавляем корневую директорию проекта в путь
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from gigachat_module.prompt import generate_greeting_image


def main():
    """Пример генерации поздравительного изображения для клиента через GigaChat"""
    
    # Создаем директорию для результатов
    os.makedirs("output/greetings", exist_ok=True)
    
    # Данные клиента и события
    # Примечание: event_type определяется автоматически по event_date
    # Для 01.01.XXXX -> "новый_год", для 08.03.XXXX -> "8_марта", для остальных -> "день_рождения"
    client_data = {
        "event_date": "01.01.2025",  # Дата события (обязательно) - тип события определится автоматически
        # "event_type": "новый_год",  # Можно указать явно, если нужно переопределить
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
    
    # Путь для сохранения изображения
    output_path = "output/greetings/gigachat_newyear_vip_client2.png"
    
    print("Генерация поздравительного изображения через GigaChat...")
    print(f"Клиент: {client_data['client_name']}")
    print(f"Компания: {client_data['company_name']}")
    print(f"Дата события: {client_data['event_date']}")
    if "event_type" in client_data:
        print(f"Тип события: {client_data['event_type']} (указан явно)")
    else:
        print("Тип события: будет определен автоматически по дате")
    print(f"Сегмент: {client_data['client_segment']}, Тон: {client_data['tone']}")
    print()
    
    try:
        # Генерируем изображение - просто передаем данные и получаем результат
        # event_type определится автоматически по event_date (01.01.2025 -> "новый_год")
        image_path = generate_greeting_image(
            output_path=output_path,
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
        
        print(f"✓ Изображение успешно сохранено: {image_path}")
        
    except Exception as e:
        print(f"✗ Ошибка: {e}")
        print("\nПроверьте:")
        print("1. Установлены ли переменные окружения GIGACHAT_CREDENTIALS или GIGACHAT_API_KEY")
        print("2. Правильность API ключей в файле .env")
        print("3. Наличие сертификата russian_trusted_root_ca_pem.crt в папке gigachat_module/")


if __name__ == "__main__":
    main()

