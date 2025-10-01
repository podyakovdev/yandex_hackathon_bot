import os

from dotenv import load_dotenv

load_dotenv()


def get_bot_token() -> str:
    token = os.environ.get("TG_TOKEN", "").strip()
    if not token:
        raise RuntimeError("Не задан токен бота (TG_TOKEN)")
    return token


def get_external_api_url() -> str:
    return os.environ.get("EXTERNAL_API_URL", "").strip()


def get_user_service_base_url() -> str:
    return os.environ.get("USER_SERVICE_BASE_URL", "").strip()


def get_user_service_timeout() -> float:
    raw = os.environ.get("USER_SERVICE_TIMEOUT", "5.0").strip()
    try:
        return float(raw)
    except ValueError:
        return 5.0
