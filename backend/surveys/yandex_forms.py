"""
Модуль для работы с Яндекс Формами
Скопирован из bot/yandex_forms.py для независимости от кода бота
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
import httpx

logger = logging.getLogger(__name__)


class YandexFormsAPI:
    """Класс для работы с API Яндекс Форм"""
    
    def __init__(self, client_id: str, client_secret: str, 
                 base_url: str = "https://api.forms.yandex.net/v1",
                 oauth_url: str = "https://oauth.yandex.ru"):
        self.client_id = client_id
        self.client_secret = client_secret
        self.oauth_url = oauth_url.rstrip('/')
        self.base_url = base_url.rstrip('/')
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
        
        url = f"{self.base_url}/forms/{survey_id}"
        headers = {
            "Authorization": f"OAuth {self.access_token}",
            "Content-Type": "application/json"
        }
        
        try:
            logger.info(f"Запрашиваем опрос {survey_id} по URL: {url}")
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(url, headers=headers)
                logger.info(f"Получен ответ: {response.status_code}")
                
                if response.status_code != 200:
                    logger.error(f"HTTP ошибка: {response.status_code}, текст: {response.text}")
                
                response.raise_for_status()
                
                data = response.json()
                logger.info(f"Получены данные опроса: {data}")
                
                # Преобразуем данные в нужный формат
                survey_data = {
                    "id": data.get("id"),
                    "title": data.get("title", f"Опрос {survey_id}"),
                    "description": data.get("description", ""),
                    "questions": self._parse_questions(data.get("questions", [])),
                    "created_at": data.get("created_at"),
                    "updated_at": data.get("updated_at")
                }
                
                logger.info(f"Обработанные данные: {survey_data}")
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
    
    def _parse_form_html(self, html_content: str, survey_id: str) -> Optional[Dict[str, Any]]:
        """
        Парсинг HTML страницы формы для извлечения вопросов
        
        Args:
            html_content: HTML содержимое страницы
            survey_id: ID формы
            
        Returns:
            Dict с данными формы или None
        """
        try:
            import re
            
            # Ищем заголовок формы
            title_match = re.search(r'<title[^>]*>([^<]+)</title>', html_content, re.IGNORECASE)
            title = title_match.group(1).strip() if title_match else f"Опрос {survey_id}"
            
            # Ищем вопросы в HTML (это упрощённый парсинг)
            # В реальности нужно более сложный парсинг
            question_patterns = [
                r'<label[^>]*>([^<]+)</label>',
                r'<span[^>]*class="[^"]*question[^"]*"[^>]*>([^<]+)</span>',
                r'<div[^>]*class="[^"]*field[^"]*"[^>]*>([^<]+)</div>'
            ]
            
            questions = []
            for pattern in question_patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                for match in matches:
                    question_text = match.strip()
                    if question_text and len(question_text) > 5:  # Фильтруем короткие тексты
                        questions.append(question_text)
            
            # Если не нашли вопросы, создаём заглушку
            if not questions:
                questions = [
                    "Вопрос 1 (автоматически извлечён)",
                    "Вопрос 2 (автоматически извлечён)",
                    "Вопрос 3 (автоматически извлечён)"
                ]
            
            return {
                "id": survey_id,
                "title": title,
                "description": f"Форма извлечена из HTML",
                "questions": questions[:10],  # Ограничиваем количество вопросов
                "created_at": None,
                "updated_at": None
            }
            
        except Exception as e:
            logger.error(f"Ошибка парсинга HTML: {e}")
            return None


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
