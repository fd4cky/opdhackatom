"""
Модуль для генерации изображений с помощью API Kandinsky
"""
import requests
import base64
import os
import json
from typing import Optional, Union

try:
    from dotenv import load_dotenv
    load_dotenv()  # Загружаем переменные из .env файла
except ImportError:
    pass  # python-dotenv не установлен, используем только переменные окружения


class KandinskyAPI:
    """Класс для работы с API Kandinsky"""
    
    def __init__(self, api_key: str, secret_key: str, api_url: str = "https://api-key.fusionbrain.ai/"):
        """
        Инициализация клиента Kandinsky API
        
        Args:
            api_key: API ключ от Fusion Brain
            secret_key: Секретный ключ от Fusion Brain
            api_url: Базовый URL API (по умолчанию Fusion Brain)
        """
        self.api_key = api_key
        self.secret_key = secret_key
        self.api_url = api_url.rstrip('/')
        self.pipeline_id = None
    
    def get_pipeline(self) -> str:
        """
        Получение pipeline ID для генерации изображений
        
        Returns:
            Pipeline ID
        """
        # Пробуем несколько вариантов endpoints
        endpoints = [
            f"{self.api_url}/key/api/v1/pipelines",
            f"{self.api_url}/key/api/v1/models",
            f"{self.api_url}/api/v1/pipelines"
        ]
        
        headers = {
            "X-Key": f"Key {self.api_key}",
            "X-Secret": f"Secret {self.secret_key}"
        }
        
        for url in endpoints:
            try:
                response = requests.get(url, headers=headers, timeout=10)
                
                if response.status_code in [200, 201]:
                    data = response.json()
                    
                    # Ищем pipeline ID в ответе
                    if isinstance(data, list) and len(data) > 0:
                        # Если ответ - массив моделей/pipelines
                        item = data[0]
                        if 'id' in item:
                            self.pipeline_id = item['id']
                            return self.pipeline_id
                        elif 'pipeline_id' in item:
                            self.pipeline_id = item['pipeline_id']
                            return self.pipeline_id
                    elif isinstance(data, dict):
                        # Если ответ - объект
                        if 'id' in data:
                            self.pipeline_id = data['id']
                            return self.pipeline_id
                        elif 'pipeline_id' in data:
                            self.pipeline_id = data['pipeline_id']
                            return self.pipeline_id
                        elif 'models' in data and isinstance(data['models'], list) and len(data['models']) > 0:
                            self.pipeline_id = data['models'][0].get('id')
                            if self.pipeline_id:
                                return self.pipeline_id
                        elif 'pipelines' in data and isinstance(data['pipelines'], list) and len(data['pipelines']) > 0:
                            self.pipeline_id = data['pipelines'][0].get('id')
                            if self.pipeline_id:
                                return self.pipeline_id
            except Exception as e:
                continue  # Пробуем следующий endpoint
        
        # Если не удалось получить pipeline, используем дефолтный или пробуем без него
        # Многие API версии не требуют pipeline ID
        self.pipeline_id = None
        return None
    
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
            width: Ширина изображения (по умолчанию 1024)
            height: Высота изображения (по умолчанию 1024)
            num_images: Количество изображений для генерации (по умолчанию 1)
            negative_prompt: Негативный промпт (опционально)
        
        Returns:
            Байты изображения (или список байтов, если num_images > 1)
        """
        # Получаем pipeline, если еще не получен
        if self.pipeline_id is None:
            self.get_pipeline()
        
        # Используем правильный endpoint для Fusion Brain API
        url = f"{self.api_url}/key/api/v1/text2image/run"
        headers = {
            "X-Key": f"Key {self.api_key}",
            "X-Secret": f"Secret {self.secret_key}"
        }
        
        # Подготовка параметров для генерации
        params_data = {
            "type": "GENERATE",
            "numImages": num_images,
            "width": width,
            "height": height,
            "generateParams": {
                "query": prompt
            }
        }
        
        if negative_prompt:
            params_data["negativePromptUnclip"] = negative_prompt
        
        # Формируем multipart/form-data запрос
        # Fusion Brain требует: pipeline_id (строка) и params (JSON)
        files = {}
        
        # Pipeline ID обязателен для Fusion Brain API
        if not self.pipeline_id:
            # Пробуем получить pipeline еще раз
            self.get_pipeline()
            if not self.pipeline_id:
                raise Exception("Не удалось получить pipeline_id. Проверьте API ключи и доступность API.")
        
        files["pipeline_id"] = (None, str(self.pipeline_id))
        files["params"] = (None, json.dumps(params_data), "application/json")
        
        # Отправка запроса на генерацию
        try:
            response = requests.post(url, headers=headers, files=files, timeout=30)
        except Exception as e:
            # Если не сработало с files, пробуем с data (обычный form-data)
            data_simple = {
                "pipeline_id": str(self.pipeline_id),
                "params": json.dumps(params_data)
            }
            response = requests.post(url, headers=headers, data=data_simple, timeout=30)
        
        if response.status_code not in [200, 201]:
            error_text = response.text[:500] if response.text else "нет текста ошибки"
            error_msg = f"Ошибка генерации: {response.status_code}, {error_text}"
            
            # Дополнительная информация для отладки
            if response.status_code == 404:
                error_msg += f"\nВозможные причины:\n"
                error_msg += f"- Неверный endpoint или API изменился\n"
                error_msg += f"- Pipeline ID: {self.pipeline_id if self.pipeline_id else 'не получен'}\n"
                error_msg += f"- URL: {url}\n"
                error_msg += f"- Проверьте правильность API ключей и доступность API"
            
            raise Exception(error_msg)
        
        result = response.json()
        uuid = result.get('uuid')
        
        if not uuid:
            raise Exception(f"Не удалось получить UUID задачи: {result}")
        
        # Ожидание завершения генерации
        return self._wait_for_generation(uuid, num_images)
    
    def _wait_for_generation(self, uuid: str, num_images: int = 1) -> Union[bytes, list[bytes]]:
        """
        Ожидание завершения генерации изображения
        
        Args:
            uuid: UUID задачи генерации
            num_images: Количество изображений
        
        Returns:
            Байты изображения (или список байтов, если num_images > 1)
        """
        import time
        
        url = f"{self.api_url}/key/api/v1/text2image/status/{uuid}"
        headers = {
            "X-Key": f"Key {self.api_key}",
            "X-Secret": f"Secret {self.secret_key}"
        }
        
        max_attempts = 60  # Максимум 60 попыток (5 минут при задержке 5 секунд)
        attempt = 0
        
        while attempt < max_attempts:
            response = requests.get(url, headers=headers)
            
            if response.status_code not in [200, 201]:
                raise Exception(f"Ошибка проверки статуса: {response.status_code}, {response.text}")
            
            result = response.json()
            status = result.get('status')
            
            if status == 'DONE':
                images = result.get('images', [])
                if not images:
                    raise Exception("Генерация завершена, но изображения не найдены")
                
                # Декодируем base64 изображения
                decoded_images = []
                for img_base64 in images:
                    decoded_images.append(base64.b64decode(img_base64))
                
                if num_images == 1:
                    return decoded_images[0]
                return decoded_images[:num_images]
            
            elif status == 'FAIL':
                error = result.get('error', 'Неизвестная ошибка')
                raise Exception(f"Ошибка генерации: {error}")
            
            # Генерация еще не завершена, ждем
            time.sleep(5)
            attempt += 1
        
        raise Exception("Превышено время ожидания генерации изображения")
    
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
        
        for i, image_bytes in enumerate(images):
            if num_images > 1:
                file_path = f"{base_path}_{i+1}{ext}"
            else:
                file_path = output_path
            
            with open(file_path, "wb") as f:
                f.write(image_bytes)
            
            saved_paths.append(file_path)
        
        if num_images == 1:
            return saved_paths[0]
        return saved_paths


def generate_image_from_prompt(
    prompt: str,
    api_key: Optional[str] = None,
    secret_key: Optional[str] = None,
    output_path: Optional[str] = None,
    width: int = 1024,
    height: int = 1024,
    negative_prompt: Optional[str] = None
) -> Union[bytes, str]:
    """
    Удобная функция для быстрой генерации изображения
    
    Args:
        prompt: Текстовое описание желаемого изображения
        api_key: API ключ от Fusion Brain
        secret_key: Секретный ключ от Fusion Brain
        output_path: Опциональный путь для сохранения файла
        width: Ширина изображения
        height: Высота изображения
        negative_prompt: Негативный промпт (опционально)
    
    Returns:
        Байты изображения или путь к файлу, если указан output_path
    """
    if not api_key or not secret_key:
        api_key, secret_key = load_api_keys_from_env()
        if not api_key or not secret_key:
            raise ValueError("Необходимо указать API ключи или создать .env файл")
    
    client = KandinskyAPI(api_key, secret_key)
    
    if output_path:
        return client.generate_and_save(prompt, output_path, width, height, negative_prompt=negative_prompt)
    else:
        return client.generate_image(prompt, width, height, negative_prompt=negative_prompt)


def load_api_keys_from_env() -> tuple[Optional[str], Optional[str]]:
    """
    Загружает API ключи из переменных окружения или .env файла
    
    Returns:
        Кортеж (api_key, secret_key) или (None, None) если ключи не найдены
    """
    api_key = os.getenv("KANDINSKY_API_KEY")
    secret_key = os.getenv("KANDINSKY_SECRET_KEY")
    return api_key, secret_key


if __name__ == "__main__":
    # Пример использования
    # Получаем ключи из переменных окружения или .env файла
    API_KEY, SECRET_KEY = load_api_keys_from_env()
    
    if not API_KEY or not SECRET_KEY:
        print("Пожалуйста, установите переменные окружения или создайте .env файл:")
        print("KANDINSKY_API_KEY=ваш_api_ключ")
        print("KANDINSKY_SECRET_KEY=ваш_secret_ключ")
        print("\nИли установите переменные окружения:")
        print("export KANDINSKY_API_KEY='ваш_ключ'")
        print("export KANDINSKY_SECRET_KEY='ваш_ключ'")
    else:
        # Создаем клиент
        try:
            client = KandinskyAPI(API_KEY, SECRET_KEY)
            
            # Генерируем изображение
            prompt = "Красивый закат над горами, цифровое искусство"
            print(f"Генерация изображения по промпту: '{prompt}'...")
            
            image_path = client.generate_and_save(
                prompt=prompt,
                output_path="output/kandinsky_image.png",
                width=1024,
                height=1024
            )
            print(f"Изображение успешно сохранено: {image_path}")
        except Exception as e:
            print(f"Ошибка: {e}")

