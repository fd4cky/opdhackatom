# Модуль для работы с API GigaChat

Модуль для генерации изображений с помощью API GigaChat от Сбербанка. Использует официальную библиотеку `gigachat` с поддержкой российского сертификата.

## Установка

```bash
pip install -r requirements.txt
```

## Настройка

### Сертификат

Сертификат для работы с GigaChat API уже включен в модуль (`gigachat/russian_trusted_root_ca_pem.crt`). Он автоматически используется при инициализации клиента.

### Получение ключей

Получите ключи авторизации на платформе [GigaChat Developers](https://developers.sber.ru/):
- Ключ авторизации (credentials/auth key) - рекомендуется
  - Это может быть прямой ключ авторизации
  - Или base64(client_id:client_secret)
- Или Client ID и Client Secret (будут автоматически преобразованы)

### Способ 1: Использование .env файла (рекомендуется)

1. Добавьте в файл `.env` один из вариантов:

**Вариант 1: Ключ авторизации / Auth Key (рекомендуется)**
```env
GIGACHAT_CREDENTIALS=ваш_ключ_авторизации
# или
GIGACHAT_API_KEY=ваш_ключ_авторизации
```
Примечание: `credentials` и `api_key` - это одно и то же (ключ авторизации / auth key)

**Вариант 2: API ключ**
```env
GIGACHAT_API_KEY=ваш_api_ключ
```

**Вариант 3: Client ID и Secret**
```env
GIGACHAT_CLIENT_ID=ваш_client_id
GIGACHAT_CLIENT_SECRET=ваш_client_secret
```

Модуль автоматически загрузит ключи из `.env` файла и использует сертификат.

### Способ 2: Переменные окружения

Установите их как переменные окружения:

```bash
export GIGACHAT_CREDENTIALS='ваш_ключ_авторизации'
# или
export GIGACHAT_API_KEY='ваш_api_ключ'
# или
export GIGACHAT_CLIENT_ID='ваш_client_id'
export GIGACHAT_CLIENT_SECRET='ваш_client_secret'
```

## Использование

### Простой способ

```python
from gigachat.gigachat_module import generate_image_from_prompt, load_api_keys_from_env

# Загрузка ключей из .env
credentials, api_key, client_id, client_secret = load_api_keys_from_env()

# Генерация и сохранение в файл
image_path = generate_image_from_prompt(
    prompt="Красивый закат над горами",
    credentials=credentials,
    output_path="output/image.png"
)
```

### Использование класса

```python
from gigachat.gigachat_module import GigaChatAPI, load_api_keys_from_env

# Загрузка ключей
credentials, api_key, client_id, client_secret = load_api_keys_from_env()

# Создание клиента (сертификат используется автоматически)
client = GigaChatAPI(credentials=credentials)

# Генерация изображения (получение байтов)
image_bytes = client.generate_image(
    prompt="Фантастический пейзаж с драконом",
    width=1024,
    height=1024
)

# Генерация и сохранение в файл
image_path = client.generate_and_save(
    prompt="Портрет в стиле ренессанс",
    output_path="output/portrait.png",
    width=1024,
    height=1024
)
```

### Использование с явным указанием сертификата

```python
from gigachat.gigachat_module import GigaChatAPI
from pathlib import Path

# Путь к сертификату
cert_path = Path(__file__).parent / "gigachat" / "russian_trusted_root_ca_pem.crt"

client = GigaChatAPI(
    credentials="ваш_ключ_авторизации",
    ca_bundle_file=str(cert_path)
)
```

## Параметры

- `prompt` (str): Текстовое описание желаемого изображения
- `width` (int): Ширина изображения в пикселях (по умолчанию 1024)
- `height` (int): Высота изображения в пикселях (по умолчанию 1024)
- `num_images` (int): Количество изображений для генерации (по умолчанию 1)
- `negative_prompt` (str, опционально): Негативный промпт (что не должно быть на изображении)
- `ca_bundle_file` (str, опционально): Путь к файлу сертификата (по умолчанию используется встроенный)

## Примеры

Запустите пример:

```bash
python gigachat/example.py
```

Убедитесь, что установлены переменные окружения с API ключами.

## Примечания

- Модуль использует официальную библиотеку `gigachat` от Сбербанка
- Сертификат для работы с API включен в модуль и используется автоматически
- При необходимости можно указать свой путь к сертификату через параметр `ca_bundle_file`
- Для работы требуется установленная библиотека `gigachat` (устанавливается через `requirements.txt`)

## Документация

Подробная документация по GigaChat API доступна на [developers.sber.ru](https://developers.sber.ru/docs/ru/gigachat/)
