# Генерация поздравительных изображений

Модуль для генерации персонализированных поздравительных изображений через API GigaChat.

## Структура проекта

```
opdhackatom/
├── gigachat_module/        # Модуль для работы с API GigaChat
│   ├── __init__.py
│   ├── gigachat_module.py  # Базовый модуль API
│   ├── prompt.py           # Формирование промптов и генерация изображений
│   ├── text_generator.py   # Генерация текста поздравлений
│   ├── sincerity_evaluator.py  # Оценка искренности текста
│   ├── prompt_template.py  # Шаблоны промптов
│   ├── README.md
│   └── russian_trusted_root_ca_pem.crt
├── telegram_bot/          # Telegram бот
│   ├── __init__.py
│   ├── bot.py             # Основной файл бота
│   └── README.md
├── examples/              # Примеры использования
│   ├── gigachat_greeting_example.py
│   ├── gigachat_text_example.py
│   └── sincerity_evaluation_example.py
├── output/                # Сгенерированные изображения
│   └── greetings/
├── .env                   # API ключи (не в репозитории)
├── .env.example           # Шаблон для .env
├── requirements.txt       # Зависимости
└── README.md
```

## Установка

```bash
pip install -r requirements.txt
```

## Настройка

Создайте файл `.env` на основе `.env.example` и заполните API ключи:

```env
# GigaChat API (один из вариантов)
GIGACHAT_CREDENTIALS=ваш_ключ_авторизации
# Или
GIGACHAT_API_KEY=ваш_api_ключ
# Или
GIGACHAT_CLIENT_ID=ваш_client_id
GIGACHAT_CLIENT_SECRET=ваш_client_secret

# Telegram Bot
TELEGRAM_BOT_TOKEN=ваш_токен_бота
```

## Использование модулей

### Способ 1: Простая функция (рекомендуется)

Самый простой способ - использовать функцию `generate_greeting_image()`:

```python
from gigachat_module.prompt import generate_greeting_image

# Генерируем изображение - передаем все данные одной функцией
image_path = generate_greeting_image(
    output_path="output/greeting.png",
    event_date="01.01.2025",  # Обязательно - тип события определится автоматически
    client_name="Иван Петров",
    company_name="ООО 'ТехноСтрой'",
    position="Генеральный директор",
    client_segment="VIP",
    tone="официальный",
    preferences=["премиум качество", "корпоративный стиль"],
    interaction_history={
        "last_contact": "2024-12-15",
        "topic": "кредитная линия"
    }
)

print(f"Изображение сохранено: {image_path}")
```

### Способ 2: Использование класса

Если нужно сгенерировать несколько изображений, используйте класс:

```python
from gigachat_module.prompt import GigaChatPrompt

# Создаем экземпляр (ключи загружаются из .env автоматически)
prompt_gen = GigaChatPrompt()

# Генерируем первое изображение
image_path1 = prompt_gen.generate(
    output_path="output/newyear.png",
    event_date="01.01.2025",  # Тип события определится автоматически (новый_год)
    company_name="ООО 'ТехноСтрой'",
    client_segment="VIP",
    tone="официальный"
)

# Генерируем второе изображение
image_path2 = prompt_gen.generate(
    output_path="output/birthday.png",
    event_date="15.03.2025",  # Тип события определится автоматически (день_рождения)
    company_name="ООО 'МедиаГрупп'",
    client_segment="лояльный",
    tone="дружеский"
)
```

### Способ 3: Telegram бот

Запустите Telegram бота:

```bash
python telegram_bot/bot.py
```

Бот будет запрашивать данные для генерации изображения и отправлять результат.

## Параметры для формирования промпта

### Обязательные параметры

- **`output_path`** (str): Путь для сохранения изображения
  - Пример: `"output/greeting.png"`

- **`event_date`** (str): Дата события в формате `DD.MM.YYYY` (обязательно)
  - Пример: `"01.01.2025"` - автоматически определится как "новый_год"
  - Пример: `"08.03.2025"` - автоматически определится как "8_марта"
  - Пример: `"15.03.2025"` - автоматически определится как "день_рождения"
  - Тип события определяется автоматически по дате

### Опциональные параметры

- **`event_type`** (str): Тип события (опционально, определяется автоматически по дате)
  - `"новый_год"` - Новый год (01.01.XXXX)
  - `"день_рождения"` - День рождения (любая другая дата)
  - `"8_марта"` - Международный женский день (08.03.XXXX)
  - `"профессиональный_праздник"` - Профессиональный праздник
  - `"юбилей"` - Юбилей компании
  - `"день_компании"` - День основания компании

- **`client_name`** (str): Имя клиента
  - Пример: `"Иван Петров"`
  - Используется для персонализации

- **`company_name`** (str): Название компании клиента
  - Пример: `"ООО 'ТехноСтрой'"`
  - Влияет на корпоративный стиль изображения

- **`position`** (str): Должность контактного лица
  - Пример: `"Генеральный директор"` или `"Финансовый директор"`
  - Влияет на стиль (руководящий уровень, финансовый сектор и т.д.)

- **`client_segment`** (str): Сегмент клиента (по умолчанию `"стандартный"`)
  - `"VIP"` - VIP-клиент (премиум качество, эксклюзивный дизайн)
  - `"новый"` - Новый клиент (приветливый, дружелюбный стиль)
  - `"лояльный"` - Лояльный клиент (благодарность, долгосрочное партнерство)
  - `"стандартный"` - Стандартный клиент (профессиональный, дружелюбный)

- **`tone`** (str): Тон поздравления (по умолчанию `"официальный"`)
  - `"официальный"` - Официальный, уважительный тон (корпоративный стиль, элегантный)
  - `"дружеский"` - Теплый, дружеский тон (приветливый, современный дизайн)
  - `"креативный"` - Креативный, оригинальный подход (яркие цвета, инновационный)

- **`preferences`** (List[str]): Предпочтения клиента
  - Пример: `["премиум качество", "корпоративный стиль", "минимализм"]`
  - Список строк с предпочтениями клиента

- **`interaction_history`** (Dict): История взаимодействий
  - Формат: `{"last_contact": "2024-12-15", "topic": "кредитная линия"}`
  - `last_contact`: Дата последнего контакта
  - `topic`: Тема взаимодействия (влияет на контекст: кредитные услуги, банковские услуги и т.д.)

## Примеры использования

### Пример 1: Новый год для VIP-клиента

```python
from gigachat_module.prompt import generate_greeting_image

image_path = generate_greeting_image(
    output_path="output/newyear_vip.png",
    event_date="01.01.2025",  # Автоматически определится как "новый_год"
    client_name="Иван Петров",
    company_name="ООО 'ТехноСтрой'",
    position="Генеральный директор",
    client_segment="VIP",
    tone="официальный",
    preferences=["премиум качество", "корпоративный стиль"],
    interaction_history={
        "last_contact": "2024-12-15",
        "topic": "кредитная линия"
    }
)
```

### Пример 2: День рождения для нового клиента

```python
from gigachat_module.prompt import generate_greeting_image

image_path = generate_greeting_image(
    output_path="output/birthday_new.png",
    event_date="15.03.2025",  # Автоматически определится как "день_рождения"
    client_name="Анна Смирнова",
    company_name="ООО 'МедиаГрупп'",
    position="Финансовый директор",
    client_segment="новый",
    tone="дружеский",
    preferences=["современный дизайн", "яркие цвета"],
    interaction_history={
        "last_contact": "2024-12-20",
        "topic": "открытие расчетного счета"
    }
)
```

### Пример 3: Минимальный набор данных

```python
from gigachat_module.prompt import generate_greeting_image

# Минимально необходимые данные
image_path = generate_greeting_image(
    output_path="output/march8.png",
    event_date="08.03.2025",  # Автоматически определится как "8_марта"
    company_name="ООО 'Цветы'",
    client_segment="лояльный",
    tone="креативный"
)
```

## Как формируется промпт

Модуль автоматически формирует промпт на основе переданных данных:

1. **Элементы события** - добавляются визуальные элементы в зависимости от типа события
   - Новый год: елка, снежинки, фейерверки
   - День рождения: торт, свечи, шары
   - 8 Марта: цветы, тюльпаны, весенняя атмосфера

2. **Стиль и тон** - определяется визуальный стиль
   - Официальный: корпоративный, элегантный, деловой
   - Дружеский: теплый, приветливый, современный
   - Креативный: оригинальный, инновационный, яркий

3. **Сегмент клиента** - добавляются особенности качества
   - VIP: премиум качество, эксклюзивный дизайн
   - Новый: приветливый, дружелюбный
   - Лояльный: благодарность, персонализация

4. **Персонализация** - учитываются данные о клиенте
   - Компания: корпоративный стиль компании
   - Должность: контекст профессии (руководство, финансы и т.д.)
   - Предпочтения: учитываются предпочтения клиента
   - История: контекст последнего взаимодействия

## Генерация текста поздравлений

Помимо генерации изображений, модуль поддерживает генерацию персонализированных текстов поздравлений:

```python
from gigachat_module.text_generator import generate_greeting_text

# Генерация текста поздравления
greeting_text = generate_greeting_text(
    event_date="01.01.2025",
    event_type="новый год",
    client_name="Иван Петров",
    company_name="ООО 'ТехноСтрой'",
    position="Генеральный директор",
    client_segment="VIP",
    tone="официальный",
    preferences=["премиум качество"]
)

print(greeting_text)
```

## Оценка искренности текста

Модуль включает функцию оценки искренности генерируемых текстов через GigaChat API. Это позволяет автоматически перегенерировать текст, если он недостаточно искренен.

### Автоматическая оценка и перегенерация

```python
from gigachat_module.text_generator import generate_greeting_text

# Генерация с автоматической оценкой искренности
greeting_text = generate_greeting_text(
    event_date="01.01.2025",
    event_type="новый год",
    client_name="Иван Петров",
    company_name="ООО 'ТехноСтрой'",
    client_segment="VIP",
    tone="официальный",
    evaluate_sincerity=True,  # Включаем оценку искренности
    min_sincerity=0.6,  # Минимальный порог искренности (0.0-1.0)
    max_retries=2  # Максимум 2 попытки перегенерации
)
```

### Ручная оценка текста

```python
from gigachat_module.sincerity_evaluator import evaluate_sincerity, is_text_sincere_enough

# Оценка уже сгенерированного текста
text = "Ваш текст поздравления..."

# Оценка с контекстом
context = {
    "event_type": "новый год",
    "client_segment": "VIP",
    "tone": "официальный"
}

scores = evaluate_sincerity(text, context=context)
print(f"Искренность: {scores['sincerity_score']:.2f}")
print(f"Теплота: {scores['warmth_score']:.2f}")
print(f"Персонализация: {scores['personalization_score']:.2f}")
print(f"Аутентичность: {scores['authenticity_score']:.2f}")

# Проверка, достаточно ли искренен текст
is_sincere, detailed_scores = is_text_sincere_enough(
    text,
    min_sincerity=0.6,
    context=context
)
```

### Метрики оценки

Оценка искренности включает 4 метрики (каждая от 0.0 до 1.0):

- **sincerity_score** - Общая оценка искренности (насколько текст звучит искренне, а не шаблонно)
- **warmth_score** - Оценка теплоты (насколько текст теплый и дружелюбный)
- **personalization_score** - Оценка персонализации (насколько текст персонализирован под конкретного клиента)
- **authenticity_score** - Оценка аутентичности (насколько текст звучит естественно и аутентично)

При использовании `is_text_sincere_enough()` используется взвешенная оценка:
- sincerity_score × 0.4
- warmth_score × 0.2
- personalization_score × 0.2
- authenticity_score × 0.2

## Запуск примеров

```bash
# Пример с GigaChat API
python examples/gigachat_greeting_example.py

# Пример генерации текста
python examples/gigachat_text_example.py

# Пример оценки искренности
python examples/sincerity_evaluation_example.py

# Запуск Telegram бота
python telegram_bot/bot.py
```

## Telegram бот

Простой Telegram бот для генерации изображений через диалог.

### Установка и запуск

1. Создайте бота через @BotFather в Telegram
2. Получите токен бота
3. Добавьте `TELEGRAM_BOT_TOKEN` в `.env` файл
4. Запустите бота:

```bash
python telegram_bot/bot.py
```

### Использование бота

1. Найдите вашего бота в Telegram
2. Отправьте `/start` для приветствия
3. Отправьте `/generate` для начала создания изображения
4. Следуйте инструкциям бота - он будет запрашивать данные пошагово
5. Получите готовое изображение!

Подробнее см. [telegram_bot/README.md](telegram_bot/README.md)

## Лицензия

Проект создан для хакатона OPD HackAtom.
