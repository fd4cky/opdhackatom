"""
Пример использования модуля оценки искренности текста
"""
import sys
from pathlib import Path

# Добавляем корневую директорию проекта в путь
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

from gigachat_module.text_generator import generate_greeting_text
from gigachat_module.sincerity_evaluator import evaluate_sincerity, is_text_sincere_enough


def main():
    """Пример использования оценки искренности"""
    
    print("=" * 60)
    print("Пример оценки искренности генерируемого текста")
    print("=" * 60)
    
    # Пример 1: Генерация текста с автоматической оценкой и перегенерацией
    print("\n1. Генерация текста с оценкой искренности (автоматическая перегенерация при низкой оценке):")
    print("-" * 60)
    
    text_with_eval = generate_greeting_text(
        event_date="01.01.2025",
        event_type="новый год",
        client_name="Иван Петров",
        company_name="ООО 'ТехноСтрой'",
        position="Генеральный директор",
        client_segment="VIP",
        tone="официальный",
        evaluate_sincerity=True,  # Включаем оценку искренности
        min_sincerity=0.6,  # Минимальный порог искренности
        max_retries=2  # Максимум 2 попытки перегенерации
    )
    
    print(f"Сгенерированный текст:\n{text_with_eval}\n")
    
    # Пример 2: Генерация текста без оценки
    print("\n2. Генерация текста без оценки искренности:")
    print("-" * 60)
    
    text_without_eval = generate_greeting_text(
        event_date="08.03.2025",
        event_type="8 марта",
        client_name="Анна Иванова",
        company_name="ООО 'МедиаГрупп'",
        position="Финансовый директор",
        client_segment="лояльный",
        tone="дружеский",
        evaluate_sincerity=False  # Оценка отключена
    )
    
    print(f"Сгенерированный текст:\n{text_without_eval}\n")
    
    # Пример 3: Ручная оценка уже сгенерированного текста
    print("\n3. Ручная оценка искренности текста:")
    print("-" * 60)
    
    test_text = (
        "Иван Петрович, С наступающим Новым годом! "
        "Пусть сверкающие звезды и звонкий смех встретят вас в этот волшебный праздник. "
        "Желаем вам крепкого здоровья, вдохновляющих идей и успешного воплощения планов — "
        "именно такие партнеры, как вы, делают наш совместный путь ярким и продуктивным. "
        "ООО «Сбер» сердечно поздравляет вас и вашу команду с грядущим торжеством, "
        "искренне желая новых высот и блестящих достижений в новом году! "
        "Пусть впереди вас ждут лишь радость, благополучие и новые горизонты!\n\n"
        "С уважением,\nСбер"
    )
    
    # Оценка с контекстом
    context = {
        "event_type": "новый год",
        "client_segment": "VIP",
        "tone": "официальный"
    }
    
    scores = evaluate_sincerity(test_text, context=context)
    
    print(f"Текст для оценки:\n{test_text}\n")
    print("Оценки искренности:")
    print(f"  - Искренность: {scores['sincerity_score']:.2f}")
    print(f"  - Теплота: {scores['warmth_score']:.2f}")
    print(f"  - Персонализация: {scores['personalization_score']:.2f}")
    print(f"  - Аутентичность: {scores['authenticity_score']:.2f}")
    
    # Проверка, достаточно ли искренен текст
    is_sincere, detailed_scores = is_text_sincere_enough(
        test_text,
        min_sincerity=0.6,
        context=context
    )
    
    print(f"\nТекст достаточно искренен (порог 0.6): {'Да' if is_sincere else 'Нет'}")
    print(f"Взвешенная оценка: {detailed_scores['sincerity_score'] * 0.4 + detailed_scores['warmth_score'] * 0.2 + detailed_scores['personalization_score'] * 0.2 + detailed_scores['authenticity_score'] * 0.2:.2f}")
    
    print("\n" + "=" * 60)
    print("Пример завершен!")
    print("=" * 60)


if __name__ == "__main__":
    main()

