import logging

import httpx

from config import (
    get_external_api_url,
    get_user_service_base_url,
    get_user_service_timeout,
)


logger = logging.getLogger(__name__)


async def call_external_api(value, payload_meta):
    url = get_external_api_url()
    if not url:
        return None
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(
                url, json={"value": value, **payload_meta}
            )
            resp.raise_for_status()
            data = resp.json()
            result = data.get("result")
            if isinstance(result, int):
                return result
            if isinstance(result, str) and result.isdigit():
                return int(result)
            return None
    except Exception as e:  # noqa: BLE001
        logger.warning(
            "Внешний API недоступен или вернул ошибку: %s", e
        )
        return None


# ---- Пользовательский сервис (Django) ----

async def get_user_by_username(username):
    base = get_user_service_base_url()
    if not base or not username:
        return None
    url = f"{base.rstrip('/')}/api/users/by-nickname/{username}/"
    try:
        async with httpx.AsyncClient(
            timeout=get_user_service_timeout()
        ) as client:
            resp = await client.get(url)
            if resp.status_code == 404:
                return None
            resp.raise_for_status()
            return resp.json()
    except Exception as e:  # noqa: BLE001
        logger.warning(
            "Не удалось получить пользователя из user-сервиса: %s", e
        )
        return None


async def create_user(tg_nickname, name, surname, age, gender):
    """Создание пользователя через API"""
    base = get_user_service_base_url()
    if not base:
        return None
    url = f"{base.rstrip('/')}/api/users/register/"
    payload = {
        "tg_nickname": tg_nickname,
        "name": name,
        "surname": surname,
        "age": age,
        "gender": gender,
    }
    try:
        async with httpx.AsyncClient(
            timeout=get_user_service_timeout()
        ) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            return resp.json()
    except Exception as e:  # noqa: BLE001
        logger.warning(
            "Не удалось создать пользователя в user-сервисе: %s", e
        )
        return None


async def submit_survey_response(survey_id, user_data, answers):
    """Отправка ответов на опрос через API"""
    base = get_user_service_base_url()
    if not base:
        return None
    url = f"{base.rstrip('/')}/api/surveys/{survey_id}/submit/"
    payload = {
        "answers": answers,
        "user_id": user_data.get("id"),
        "telegram_user_id": str(user_data.get("user_id", "")),
        "telegram_username": user_data.get("username", ""),
    }
    try:
        async with httpx.AsyncClient(
            timeout=get_user_service_timeout()
        ) as client:
            resp = await client.post(url, json=payload)
            resp.raise_for_status()
            return resp.json()
    except Exception as e:  # noqa: BLE001
        logger.warning(
            "Не удалось отправить ответы на опрос: %s", e
        )
        return None

