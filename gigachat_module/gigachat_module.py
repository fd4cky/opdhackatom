"""
Модуль для генерации изображений с помощью API GigaChat
Использует официальную библиотеку gigachat
"""
import os
from typing import Optional, Union
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv()  # Загружаем переменные из .env файла
except ImportError:
    pass  # python-dotenv не установлен, используем только переменные окружения

try:
    # Импортируем из системной библиотеки gigachat
    import sys
    import importlib
    
    # Временно удаляем локальную папку из пути, чтобы импортировать системную библиотеку
    original_path = sys.path.copy()
    if str(Path(__file__).parent.parent) in sys.path:
        sys.path.remove(str(Path(__file__).parent.parent))
    
    from gigachat import GigaChat
    GIGACHAT_AVAILABLE = True
    
    # Восстанавливаем путь
    sys.path = original_path
except ImportError:
    GIGACHAT_AVAILABLE = False
    GigaChat = None


# Путь к сертификату
CERT_PATH = Path(__file__).parent / "russian_trusted_root_ca_pem.crt"


class GigaChatAPI:
    """Класс для работы с API GigaChat для генерации изображений"""
    
    def __init__(
        self, 
        credentials: Optional[str] = None,
        api_key: Optional[str] = None,
        client_id: Optional[str] = None,
        client_secret: Optional[str] = None,
        scope: str = "GIGACHAT_API_PERS",
        model: str = "GigaChat",
        ca_bundle_file: Optional[str] = None
    ):
        """
        Инициализация клиента GigaChat API
        
        Args:
            credentials: Ключ авторизации (auth key) - строка в формате base64(client_id:client_secret)
                        или прямой ключ авторизации (приоритет)
            api_key: API ключ (альтернатива credentials, синоним)
            client_id: Client ID от GigaChat (будет преобразован в credentials)
            client_secret: Client Secret от GigaChat (будет преобразован в credentials)
            scope: Область доступа (по умолчанию GIGACHAT_API_PERS)
            model: Модель для использования (по умолчанию GigaChat)
            ca_bundle_file: Путь к файлу сертификата (по умолчанию используется встроенный)
        """
        if not GIGACHAT_AVAILABLE:
            raise ImportError(
                "Библиотека gigachat не установлена. Установите её командой:\n"
                "pip install gigachat"
            )
        
        # Определяем ключ авторизации (auth key)
        # credentials и api_key - это одно и то же (ключ авторизации)
        auth_key = credentials or api_key
        
        if not auth_key and (not client_id or not client_secret):
            raise ValueError(
                "Необходимо указать один из вариантов:\n"
                "- credentials или api_key (ключ авторизации / auth key)\n"
                "- client_id и client_secret (будут преобразованы в credentials)"
            )
        
        # Определяем путь к сертификату
        if ca_bundle_file:
            cert_path = ca_bundle_file
        elif CERT_PATH.exists():
            cert_path = str(CERT_PATH)
        else:
            cert_path = None
        
        # Создаем клиент GigaChat
        try:
            if auth_key:
                # Используем ключ авторизации (auth key) напрямую
                # Это может быть base64(client_id:client_secret) или прямой ключ
                self.client = GigaChat(
                    credentials=auth_key,  # auth key
                    scope=scope,
                    model=model,
                    ca_bundle_file=cert_path
                )
            else:
                # Используем client_id и client_secret
                # Формируем credentials (auth key) в формате base64(client_id:client_secret)
                import base64
                credentials_b64 = base64.b64encode(
                    f"{client_id}:{client_secret}".encode()
                ).decode()
                
                self.client = GigaChat(
                    credentials=credentials_b64,  # auth key = base64(client_id:client_secret)
                    scope=scope,
                    model=model,
                    ca_bundle_file=cert_path
                )
        except Exception as e:
            raise Exception(f"Ошибка инициализации GigaChat клиента: {e}")
    
    def generate_image(
        self,
        prompt: str,
        width: int = 1024,
        height: int = 1024,
        num_images: int = 1,
        negative_prompt: Optional[str] = None
    ) -> Union[bytes, list[bytes]]:
        """
        Генерация изображения по текстовому промпту
        
        Args:
            prompt: Текстовое описание желаемого изображения
            width: Ширина изображения
            height: Высота изображения
            num_images: Количество изображений для генерации
            negative_prompt: Негативный промпт (что не должно быть на изображении)
        
        Returns:
            Байты изображения (или список байтов, если num_images > 1)
        """
        # Формируем промпт для генерации изображения
        # GigaChat требует использования глагола "нарисуй" для вызова функции text2image
        # ВАЖНО: Подчеркиваем, что текст НЕ ДОЛЖЕН присутствовать на изображении
        image_prompt = f"Нарисуй {prompt}. КРИТИЧЕСКИ ВАЖНО: на изображении НЕ ДОЛЖНО быть никакого текста, никаких надписей, никаких слов, никаких букв, никаких цифр - только визуальные элементы."
        if negative_prompt:
            image_prompt = f"Нарисуй {prompt}. КРИТИЧЕСКИ ВАЖНО: на изображении НЕ ДОЛЖНО быть никакого текста, никаких надписей, никаких слов, никаких букв, никаких цифр - только визуальные элементы. Строго исключи: {negative_prompt}"
        
        # Используем chat API для генерации изображения
        # GigaChat генерирует изображения через chat с function_call="auto"
        # Это автоматически вызовет функцию text2image
        # Согласно документации: нужно передать словарь с messages и function_call="auto"
        try:
            # Формируем запрос в формате, который ожидает GigaChat API
            # Используем простой словарь - библиотека gigachat принимает словарь напрямую
            chat_payload = {
                "messages": [
                    {"role": "user", "content": image_prompt}
                ],
                "function_call": "auto"
            }
            
            # Передаем словарь напрямую в chat() - библиотека сама преобразует его
            response = self.client.chat(chat_payload)
        except Exception as e:
            error_msg = str(e).lower()
            # Если ошибка соединения, пробуем еще раз
            if "connection" in error_msg or "reset" in error_msg or "peer" in error_msg:
                # Пробуем еще раз с простым запросом
                try:
                    from gigachat.models import Chat, Messages, MessagesRole
                    messages_list = [Messages(role=MessagesRole.USER, content=image_prompt)]
                    chat_request = Chat(messages=messages_list, function_call="auto")
                    response = self.client.chat(chat_request)
                except Exception as retry_error:
                    raise Exception(
                        f"Ошибка соединения с GigaChat API: {e}\n"
                        f"Повторная попытка также не удалась: {retry_error}\n"
                        f"Проверьте:\n"
                        f"1. Подключение к интернету\n"
                        f"2. Правильность API ключей\n"
                        f"3. Доступность сервиса GigaChat"
                    )
            elif "timeout" in error_msg or "timed out" in error_msg:
                raise Exception(
                    f"Таймаут при генерации изображения. Генерация изображений через GigaChat может занимать много времени.\n"
                    f"Попробуйте:\n"
                    f"1. Упростить промпт\n"
                    f"2. Проверить подключение к интернету\n"
                    f"3. Повторить запрос позже"
                )
            else:
                raise Exception(f"Ошибка при вызове chat API: {e}")
        
        # Обработка ответа
        # Ответ должен содержать file_id для скачивания изображения
        try:
            if hasattr(response, 'choices') and len(response.choices) > 0:
                message = response.choices[0].message
                content = message.content if hasattr(message, 'content') else str(message)
                
                # ПРИОРИТЕТ 1: Проверяем function_call ПЕРВЫМ - это основной способ получения file_id
                if hasattr(message, 'function_call') and message.function_call:
                    # function_call содержит информацию о вызванной функции text2image
                    function_name = None
                    if hasattr(message.function_call, 'name'):
                        function_name = message.function_call.name
                    
                    # Извлекаем file_id из arguments
                    if hasattr(message.function_call, 'arguments'):
                        import json
                        try:
                            # arguments может быть строкой JSON или уже словарем
                            args = message.function_call.arguments
                            
                            # Отладочная информация (можно убрать позже)
                            # print(f"DEBUG: function_call.name = {function_name}")
                            # print(f"DEBUG: function_call.arguments type = {type(args)}")
                            # print(f"DEBUG: function_call.arguments = {args}")
                            
                            if isinstance(args, str):
                                args = json.loads(args)
                            
                            # Ищем file_id в разных возможных форматах
                            file_id = None
                            if isinstance(args, dict):
                                file_id = args.get('file_id') or args.get('fileId') or args.get('id') or args.get('image_id')
                            elif isinstance(args, str):
                                # Пробуем распарсить как JSON
                                try:
                                    args_dict = json.loads(args)
                                    file_id = args_dict.get('file_id') or args_dict.get('fileId') or args_dict.get('id') or args_dict.get('image_id')
                                except:
                                    # Пробуем найти file_id в строке напрямую
                                    import re
                                    file_id_match = re.search(r'["\']?file[_-]?id["\']?\s*:\s*["\']?([a-zA-Z0-9_-]+)', args, re.IGNORECASE)
                                    if file_id_match:
                                        file_id = file_id_match.group(1)
                            
                            if file_id:
                                result = self._download_image_by_id(file_id)
                                if result:
                                    return result
                        except Exception as e:
                            # Если не удалось извлечь из arguments, пробуем другие способы
                            pass
                
                # ПРИОРИТЕТ 2: Проверяем attachments - там может быть file_id или изображение
                if hasattr(message, 'attachments') and message.attachments:
                    for attachment in message.attachments:
                        # Проверяем разные форматы attachments
                        file_id = None
                        if hasattr(attachment, 'file_id') and attachment.file_id:
                            file_id = attachment.file_id
                        elif hasattr(attachment, 'id') and attachment.id:
                            file_id = attachment.id
                        elif isinstance(attachment, dict):
                            file_id = attachment.get('file_id') or attachment.get('id')
                        
                        if file_id:
                            return self._download_image_by_id(file_id)
                
                # ПРИОРИТЕТ 3: Извлекаем file_id из content
                # file_id может быть в content или в другом поле
                import re
                
                # Вариант 1: file_id напрямую в content (строка с ID)
                # Проверяем, является ли content просто file_id
                if isinstance(content, str) and len(content) > 0:
                    # Убираем пробелы и переносы строк
                    file_id = content.strip()
                    
                    # Если это похоже на file_id (UUID или другой формат)
                    if re.match(r'^[a-zA-Z0-9_-]+$', file_id) and len(file_id) > 10:
                        result = self._download_image_by_id(file_id)
                        if result:
                            return result
                    
                    # Ищем file_id в тексте
                    file_id_match = re.search(r'file[_-]?id["\s:]+([a-zA-Z0-9_-]+)', content, re.IGNORECASE)
                    if file_id_match:
                        file_id = file_id_match.group(1)
                        result = self._download_image_by_id(file_id)
                        if result:
                            return result
                    
                    # Ищем UUID-подобный формат
                    uuid_match = re.search(r'([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})', content, re.IGNORECASE)
                    if uuid_match:
                        file_id = uuid_match.group(1)
                        result = self._download_image_by_id(file_id)
                        if result:
                            return result
                
                
                # Вариант 3: Изображение в base64
                import base64
                base64_match = re.search(r'data:image/[^;]+;base64,([A-Za-z0-9+/=]+)', content, re.IGNORECASE)
                if base64_match:
                    image_bytes = base64.b64decode(base64_match.group(1))
                    if num_images == 1:
                        return image_bytes
                    return [image_bytes]
                
                # Вариант 4: URL изображения
                url_match = re.search(r'https?://[^\s<>"]+\.(jpg|jpeg|png|gif|webp)', content, re.IGNORECASE)
                if url_match:
                    import requests
                    img_url = url_match.group(0)
                    img_response = requests.get(img_url, verify=False, timeout=120)
                    image_bytes = img_response.content
                    if num_images == 1:
                        return image_bytes
                    return [image_bytes]
            
                # Если не удалось найти изображение, выводим более подробную информацию
                content_preview = str(content)[:500] if isinstance(content, str) else str(content)
                raise Exception(
                    f"GigaChat вернул текстовое описание вместо изображения.\n"
                    f"Это может означать, что:\n"
                    f"1. GigaChat не поддерживает генерацию изображений через chat API\n"
                    f"2. Нужно использовать другой метод или модель для генерации изображений\n"
                    f"3. Промпт должен быть в другом формате\n\n"
                    f"Содержимое ответа (первые 500 символов):\n{content_preview}\n\n"
                    f"Проверьте правильность промпта и API ключей."
                )
            else:
                raise Exception(f"Неожиданный формат ответа от GigaChat API. Ответ: {response}")
        except Exception as e:
            raise Exception(f"Ошибка обработки ответа от GigaChat: {e}")
    
    def _download_image_by_id(self, file_id: str) -> bytes:
        """
        Скачивание изображения по ID
        
        Args:
            file_id: ID файла изображения
        
        Returns:
            Байты изображения
        """
        if not file_id:
            raise Exception("file_id не может быть пустым")
        try:
            # Используем встроенный метод get_image из библиотеки gigachat
            # get_image возвращает Image объект с content в base64 (строка)
            if hasattr(self.client, 'get_image'):
                try:
                    image_response = self.client.get_image(file_id)
                    
                    # Image объект имеет поле content типа str с base64 строкой
                    import base64
                    
                    # Получаем content (это base64 строка)
                    if hasattr(image_response, 'content'):
                        content = image_response.content
                        
                        # content - это строка в base64, декодируем её
                        if isinstance(content, str):
                            # Убираем префикс data:image/...;base64, если есть
                            if ',' in content:
                                content = content.split(',', 1)[1]
                            # Декодируем base64 в байты
                            return base64.b64decode(content)
                        elif isinstance(content, bytes):
                            # Если уже байты, возвращаем как есть
                            return content
                        else:
                            # Пробуем преобразовать в строку и декодировать
                            content_str = str(content)
                            if ',' in content_str:
                                content_str = content_str.split(',', 1)[1]
                            return base64.b64decode(content_str)
                    else:
                        raise Exception("Не удалось найти поле content в ответе get_image")
                except Exception as e:
                    # Если get_image не работает, пробуем через requests
                    # Не логируем, чтобы не засорять вывод
                    pass
            
            # Fallback: используем requests напрямую
            import requests
            
            # URL для получения файла
            url = f"https://gigachat.devices.sberbank.ru/api/v1/files/{file_id}/content"
            
            # Получаем токен доступа из клиента
            access_token = None
            if hasattr(self.client, 'access_token'):
                access_token = self.client.access_token
            elif hasattr(self.client, '_access_token'):
                access_token = self.client._access_token
            elif hasattr(self.client, 'get_token'):
                token_response = self.client.get_token()
                if hasattr(token_response, 'access_token'):
                    access_token = token_response.access_token
                elif isinstance(token_response, dict):
                    access_token = token_response.get('access_token')
            
            if not access_token:
                raise Exception("Не удалось получить токен доступа для скачивания изображения")
            
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Accept": "image/jpeg, image/png, image/jpg, application/jpg"
            }
            
            # Используем сертификат, если он указан
            verify = False  # По умолчанию отключаем проверку SSL
            if hasattr(self.client, 'ca_bundle_file') and self.client.ca_bundle_file:
                verify = self.client.ca_bundle_file
            
            # Увеличиваем таймаут для скачивания изображения (может быть большой файл)
            response = requests.get(url, headers=headers, verify=verify, timeout=120)
            
            if response.status_code == 200:
                return response.content
            else:
                raise Exception(f"Ошибка скачивания изображения: {response.status_code}, {response.text}")
        except Exception as e:
            raise Exception(f"Ошибка при скачивании изображения по ID: {e}")
    
    def generate_and_save(
        self,
        prompt: str,
        output_path: str,
        width: int = 1024,
        height: int = 1024,
        num_images: int = 1,
        negative_prompt: Optional[str] = None
    ) -> Union[str, list[str]]:
        """
        Генерация изображения и сохранение в файл
        
        Args:
            prompt: Текстовое описание желаемого изображения
            output_path: Путь для сохранения (если num_images > 1, будет добавлен индекс)
            width: Ширина изображения
            height: Высота изображения
            num_images: Количество изображений для генерации
            negative_prompt: Негативный промпт (опционально)
        
        Returns:
            Путь к сохраненному файлу (или список путей, если num_images > 1)
        """
        images = self.generate_image(prompt, width, height, num_images, negative_prompt)
        
        if num_images == 1:
            images = [images]
        
        saved_paths = []
        base_path, ext = os.path.splitext(output_path)
        if not ext:
            ext = ".png"
        
        for i, image_data in enumerate(images):
            if num_images > 1:
                file_path = f"{base_path}_{i+1}{ext}"
            else:
                file_path = output_path
            
            # Проверяем, что данные не None
            if image_data is None:
                raise Exception(
                    f"Не удалось получить изображение (получен None). "
                    f"GigaChat API не вернул изображение для промпта. "
                    f"Возможно, GigaChat не поддерживает генерацию изображений через chat API, "
                    f"или требуется другой метод генерации."
                )
            
            # Убеждаемся, что это байты, а не строка
            if isinstance(image_data, str):
                # Если это строка, пробуем декодировать base64 или просто encode
                import base64
                try:
                    image_bytes = base64.b64decode(image_data)
                except:
                    image_bytes = image_data.encode('utf-8')
            elif isinstance(image_data, bytes):
                image_bytes = image_data
            else:
                # Пробуем преобразовать в байты
                try:
                    image_bytes = bytes(image_data)
                except (TypeError, ValueError) as e:
                    raise Exception(
                        f"Не удалось преобразовать данные изображения в байты. "
                        f"Тип данных: {type(image_data)}, значение: {image_data}. "
                        f"Ошибка: {e}"
                    )
            
            with open(file_path, "wb") as f:
                f.write(image_bytes)
            
            saved_paths.append(file_path)
        
        if num_images == 1:
            return saved_paths[0]
        return saved_paths


def generate_image_from_prompt(
    prompt: str,
    credentials: Optional[str] = None,
    api_key: Optional[str] = None,
    client_id: Optional[str] = None,
    client_secret: Optional[str] = None,
    output_path: Optional[str] = None,
    width: int = 1024,
    height: int = 1024,
    negative_prompt: Optional[str] = None
) -> Union[bytes, str]:
    """
    Удобная функция для быстрой генерации изображения
    
    Args:
        prompt: Текстовое описание желаемого изображения
        credentials: Ключ авторизации
        api_key: API ключ (альтернатива credentials)
        client_id: Client ID от GigaChat
        client_secret: Client Secret от GigaChat
        output_path: Опциональный путь для сохранения файла
        width: Ширина изображения
        height: Высота изображения
        negative_prompt: Негативный промпт (опционально)
    
    Returns:
        Байты изображения или путь к файлу, если указан output_path
    """
    client = GigaChatAPI(
        credentials=credentials,
        api_key=api_key,
        client_id=client_id,
        client_secret=client_secret
    )
    
    if output_path:
        return client.generate_and_save(prompt, output_path, width, height, negative_prompt=negative_prompt)
    else:
        return client.generate_image(prompt, width, height, negative_prompt=negative_prompt)


def load_api_keys_from_env() -> tuple[Optional[str], Optional[str], Optional[str], Optional[str]]:
    """
    Загружает API ключи из переменных окружения или .env файла
    
    Returns:
        Кортеж (credentials, api_key, client_id, client_secret) или (None, None, None, None) если ключи не найдены
    """
    credentials = os.getenv("GIGACHAT_CREDENTIALS")
    api_key = os.getenv("GIGACHAT_API_KEY")
    client_id = os.getenv("GIGACHAT_CLIENT_ID")
    client_secret = os.getenv("GIGACHAT_CLIENT_SECRET")
    return credentials, api_key, client_id, client_secret


if __name__ == "__main__":
    # Пример использования
    # Получаем ключи из переменных окружения или .env файла
    CREDENTIALS, API_KEY, CLIENT_ID, CLIENT_SECRET = load_api_keys_from_env()
    
    if not CREDENTIALS and not API_KEY and (not CLIENT_ID or not CLIENT_SECRET):
        print("Пожалуйста, установите переменные окружения или создайте .env файл:")
        print("GIGACHAT_CREDENTIALS=ваш_ключ_авторизации (auth key)")
        print("Или:")
        print("GIGACHAT_API_KEY=ваш_api_ключ (то же самое, что credentials)")
        print("Или:")
        print("GIGACHAT_CLIENT_ID=ваш_client_id")
        print("GIGACHAT_CLIENT_SECRET=ваш_client_secret")
        print("\nПримечание: credentials/auth key может быть base64(client_id:client_secret)")
        print("\nИли установите переменные окружения:")
        print("export GIGACHAT_CREDENTIALS='ваш_ключ'")
    else:
        # Создаем клиент
        try:
            client = GigaChatAPI(
                credentials=CREDENTIALS,
                api_key=API_KEY,
                client_id=CLIENT_ID,
                client_secret=CLIENT_SECRET
            )
            
            # Генерируем изображение
            prompt = "Красивый закат над горами, цифровое искусство"
            print(f"Генерация изображения по промпту: '{prompt}'...")
            
            image_path = client.generate_and_save(
                prompt=prompt,
                output_path="output/gigachat_image.png",
                width=1024,
                height=1024
            )
            print(f"Изображение успешно сохранено: {image_path}")
        except Exception as e:
            print(f"Ошибка: {e}")
