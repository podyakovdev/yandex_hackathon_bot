"""
Модуль для работы с Яндекс Формами
Предназначен для интеграции с бекендом

Для получения OAuth credentials:
1. Перейдите в https://oauth.yandex.ru/
2. Создайте новое приложение
3. Выберите тип "Серверное приложение"
4. Укажите права доступа: forms:read, forms:write
5. Получите Client ID и Client Secret
6. Используйте их в конструкторе YandexFormsAPI

Документация API: https://yandex.ru/dev/forms/doc/
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
import httpx

logger = logging.getLogger(__name__)


class YandexFormsAPI:
    """Класс для работы с API Яндекс Форм"""
    
    def __init__(self, client_id: str, client_secret: str, 
                 base_url: str = "https://forms.yandex.ru/api",
                 oauth_url: str = "https://oauth.yandex.ru"):
        self.client_id = client_id
        self.client_secret = client_secret
        self.base_url = base_url.rstrip('/')
        self.oauth_url = oauth_url.rstrip('/')
        self.timeout = 10.0
        self.access_token = None
        self.token_expires_at = None
    
    async def _ensure_authenticated(self) -> bool:
        """
        Убедиться что мы авторизованы, если нет - получить токен
        
        Returns:
            True если авторизация успешна
        """
        if self.access_token and self.token_expires_at:
            from datetime import datetime
            if datetime.now() < self.token_expires_at:
                return True
        
        return await self._get_access_token()
    
    async def _get_access_token(self) -> bool:
        """
        Получить access token через OAuth 2.0 Client Credentials
        
        Returns:
            True если токен получен успешно
        """
        token_url = f"{self.oauth_url}/token"
        
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "scope": "forms:read forms:write"  # Права для чтения и записи форм
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    token_url,
                    data=data,
                    headers={"Content-Type": "application/x-www-form-urlencoded"}
                )
                response.raise_for_status()
                
                token_data = response.json()
                self.access_token = token_data["access_token"]
                
                # Устанавливаем время истечения токена (с запасом 5 минут)
                expires_in = token_data.get("expires_in", 3600) - 300
                from datetime import datetime, timedelta
                self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
                
                logger.info("Успешно получен access token для Яндекс Форм")
                return True
                
        except httpx.HTTPStatusError as e:
            logger.error(f"Ошибка авторизации в Яндекс Формах: {e}")
            if e.response.status_code == 401:
                logger.error("Неверные client_id или client_secret")
            return False
        except Exception as e:
            logger.error(f"Ошибка при получении токена: {e}")
            return False
    
    async def get_survey(self, survey_id: str) -> Optional[Dict[str, Any]]:
        """
        Получить данные опроса по ID
        
        Args:
            survey_id: ID опроса в Яндекс Формах
            
        Returns:
            Dict с данными опроса или None при ошибке
        """
        # Убеждаемся что мы авторизованы
        if not await self._ensure_authenticated():
            logger.error("Не удалось авторизоваться в Яндекс Формах")
            return None
        
        url = f"{self.base_url}/surveys/{survey_id}"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                
                data = response.json()
                
                # Преобразуем данные в нужный формат
                survey_data = {
                    "id": data.get("id"),
                    "title": data.get("title", f"Опрос {survey_id}"),
                    "description": data.get("description", ""),
                    "questions": self._parse_questions(data.get("questions", [])),
                    "created_at": data.get("created_at"),
                    "updated_at": data.get("updated_at")
                }
                
                return survey_data
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                logger.warning(f"Опрос {survey_id} не найден")
            else:
                logger.error(f"HTTP ошибка при получении опроса {survey_id}: {e}")
            return None
        except Exception as e:
            logger.error(f"Ошибка при получении опроса {survey_id}: {e}")
            return None
    
    def _parse_questions(self, questions_data: List[Dict]) -> List[str]:
        """
        Парсинг вопросов из API Яндекс Форм
        
        Args:
            questions_data: Список вопросов из API
            
        Returns:
            Список текстов вопросов
        """
        questions = []
        for question in questions_data:
            # Извлекаем текст вопроса
            question_text = question.get("text", "")
            if question_text:
                questions.append(question_text)
            
            # Обрабатываем подвопросы если есть
            subquestions = question.get("subquestions", [])
            for subq in subquestions:
                subq_text = subq.get("text", "")
                if subq_text:
                    questions.append(f"  - {subq_text}")
        
        return questions
    
    async def submit_answers(self, survey_id: str, user_data: Dict[str, Any], 
                           answers: List[str]) -> bool:
        """
        Отправить ответы на опрос
        
        Args:
            survey_id: ID опроса
            user_data: Данные пользователя (user_id, username, etc.)
            answers: Список ответов пользователя
            
        Returns:
            True если отправка успешна, False иначе
        """
        # Убеждаемся что мы авторизованы
        if not await self._ensure_authenticated():
            logger.error("Не удалось авторизоваться в Яндекс Формах")
            return False
        
        url = f"{self.base_url}/surveys/{survey_id}/responses"
        headers = {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }
        
        # Формируем payload для отправки
        payload = {
            "survey_id": survey_id,
            "user_id": user_data.get("user_id"),
            "username": user_data.get("username"),
            "telegram_id": user_data.get("telegram_id"),
            "answers": answers,
            "submitted_at": self._get_current_timestamp(),
            "metadata": {
                "source": "telegram_bot",
                "user_agent": "yandex_hackathon_bot/1.0"
            }
        }
        
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
                
                result = response.json()
                logger.info(f"Ответы на опрос {survey_id} успешно отправлены")
                return True
                
        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP ошибка при отправке ответов: {e}")
            return False
        except Exception as e:
            logger.error(f"Ошибка при отправке ответов: {e}")
            return False
    
    def _get_current_timestamp(self) -> str:
        """Получить текущую дату в ISO формате"""
        from datetime import datetime
        return datetime.now().isoformat()


# Функции для удобного использования
async def get_survey_from_yandex(survey_id: str, client_id: str, 
                                client_secret: str) -> Optional[Dict[str, Any]]:
    """
    Получить опрос из Яндекс Форм
    
    Args:
        survey_id: ID опроса
        client_id: Client ID для OAuth
        client_secret: Client Secret для OAuth
        
    Returns:
        Данные опроса или None
    """
    api = YandexFormsAPI(client_id, client_secret)
    return await api.get_survey(survey_id)


async def submit_answers_to_yandex(survey_id: str, user_data: Dict[str, Any], 
                                 answers: List[str], client_id: str, 
                                 client_secret: str) -> bool:
    """
    Отправить ответы в Яндекс Формы
    
    Args:
        survey_id: ID опроса
        user_data: Данные пользователя
        answers: Ответы пользователя
        client_id: Client ID для OAuth
        client_secret: Client Secret для OAuth
        
    Returns:
        True если успешно
    """
    api = YandexFormsAPI(client_id, client_secret)
    return await api.submit_answers(survey_id, user_data, answers)


# Пример использования
async def main():
    """Пример использования модуля"""
    
    # Настройки OAuth (получить в Яндекс.Паспорте)
    CLIENT_ID = "your_yandex_client_id_here"
    CLIENT_SECRET = "your_yandex_client_secret_here"
    SURVEY_ID = "12345"
    
    # Получаем опрос
    survey = await get_survey_from_yandex(SURVEY_ID, CLIENT_ID, CLIENT_SECRET)
    if survey:
        print(f"Опрос: {survey['title']}")
        print(f"Вопросов: {len(survey['questions'])}")
        for i, question in enumerate(survey['questions'], 1):
            print(f"{i}. {question}")
    else:
        print("Не удалось получить опрос")
        return
    
    # Отправляем ответы
    user_data = {
        "user_id": 123456,
        "username": "test_user",
        "telegram_id": 123456
    }
    
    answers = [
        "Иван Иванов",
        "25 лет",
        "Синий",
        "IT компания"
    ]
    
    success = await submit_answers_to_yandex(
        SURVEY_ID, user_data, answers, CLIENT_ID, CLIENT_SECRET
    )
    
    if success:
        print("Ответы успешно отправлены!")
    else:
        print("Ошибка отправки ответов")


if __name__ == "__main__":
    asyncio.run(main())
