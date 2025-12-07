# Генерация поздравительных изображений

Модули для генерации персонализированных поздравительных изображений через API Kandinsky и GigaChat.

## Структура проекта

```
opdhackatom/
├── kandinsky_module/       # Модуль для работы с API Kandinsky
│   ├── __init__.py
│   ├── kandinsky_module.py  # Базовый модуль API
│   └── prompt.py            # Формирование промптов и генерация
├── gigachat_module/        # Модуль для работы с API GigaChat
│   ├── __init__.py
│   ├── gigachat_module.py  # Базовый модуль API
│   ├── prompt.py           # Формирование промптов и генерация
│   ├── README.md
│   └── russian_trusted_root_ca_pem.crt
├── examples/              # Примеры использования
│   └── greeting_prompt_example.py
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
# Kandinsky API
KANDINSKY_API_KEY=ваш_api_ключ
KANDINSKY_SECRET_KEY=ваш_secret_ключ

# GigaChat API (один из вариантов)
GIGACHAT_CREDENTIALS=ваш_ключ_авторизации
# Или
GIGACHAT_API_KEY=ваш_api_ключ
# Или
GIGACHAT_CLIENT_ID=ваш_client_id
GIGACHAT_CLIENT_SECRET=ваш_client_secret
```

## Использование модулей

### Способ 1: Простая функция (рекомендуется)

Самый простой способ - использовать функцию `generate_greeting_image()`:

```python
from kandinsky_module.prompt import generate_greeting_image

# Генерируем изображение - передаем все данные одной функцией
image_path = generate_greeting_image(
    event_type="новый_год",
    output_path="output/greeting.png",
    event_date="01.01.2025",
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
from kandinsky_module.prompt import KandinskyPrompt

# Создаем экземпляр (ключи загружаются из .env автоматически)
prompt_gen = KandinskyPrompt()

# Генерируем первое изображение
image_path1 = prompt_gen.generate(
    event_type="новый_год",
    output_path="output/newyear.png",
    event_date="01.01.2025",
    company_name="ООО 'ТехноСтрой'",
    client_segment="VIP",
    tone="официальный"
)

# Генерируем второе изображение
image_path2 = prompt_gen.generate(
    event_type="день_рождения",
    output_path="output/birthday.png",
    event_date="15.03.2025",
    company_name="ООО 'МедиаГрупп'",
    client_segment="лояльный",
    tone="дружеский"
)
```

## Параметры для формирования промпта

### Обязательные параметры

- **`event_type`** (str): Тип события
  - `"новый_год"` - Новый год
  - `"день_рождения"` - День рождения
  - `"8_марта"` - Международный женский день
  - `"профессиональный_праздник"` - Профессиональный праздник
  - `"юбилей"` - Юбилей компании
  - `"день_компании"` - День основания компании

- **`output_path`** (str): Путь для сохранения изображения
  - Пример: `"output/greeting.png"`

### Опциональные параметры

- **`event_date`** (str): Дата события в формате `DD.MM.YYYY`
  - Пример: `"01.01.2025"`
  - Если не указано, используется стандартная дата для события

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
from kandinsky_module.prompt import generate_greeting_image

image_path = generate_greeting_image(
    event_type="новый_год",
    output_path="output/newyear_vip.png",
    event_date="01.01.2025",
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
from kandinsky_module.prompt import generate_greeting_image

image_path = generate_greeting_image(
    event_type="день_рождения",
    output_path="output/birthday_new.png",
    event_date="15.03.2025",
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
from kandinsky_module.prompt import generate_greeting_image

# Минимально необходимые данные
image_path = generate_greeting_image(
    event_type="8_марта",
    output_path="output/march8.png",
    event_date="08.03.2025",
    company_name="ООО 'Цветы'",
    client_segment="лояльный",
    tone="креативный"
)
```

### Пример 4: Использование GigaChat API

```python
from gigachat_module.prompt import generate_greeting_image

# Аналогично Kandinsky, но использует GigaChat API
image_path = generate_greeting_image(
    event_type="новый_год",
    output_path="output/gigachat_newyear.png",
    event_date="01.01.2025",
    company_name="ООО 'ТехноСтрой'",
    client_segment="VIP",
    tone="официальный"
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

## Запуск примеров

```bash
# Пример с Kandinsky API
python examples/greeting_prompt_example.py

# Пример с GigaChat API
python examples/gigachat_greeting_example.py
```

## Разница между Kandinsky и GigaChat

- **Kandinsky**: Промпты на английском языке, быстрая генерация
- **GigaChat**: Промпты на русском языке, требует сертификат для работы

Оба модуля имеют одинаковый интерфейс, можно использовать любой.

## Лицензия

Проект создан для хакатона OPD HackAtom.
