import httpx


YANDEX_FORM_API = "https://forms.yandex.ru/api/v1/submit"
YANDEX_TTS_URL = "https://tts.api.cloud.yandex.net/speech/v1/tts:synthesize"
YANDEX_STT_URL = "https://stt.api.cloud.yandex.net/speech/v1/stt:recognize"


async def send_to_yandex(form_id: str, payload: dict) -> bool:
    "Преобразует текст в речь"
    async with httpx.AsyncClient() as client:
        response = await client.post(f"{YANDEX_FORM_API}/{form_id}", json=payload)
        return response.status_code == 200


async def synthesize(text: str, token: str) -> bytes:
    "Распознает речь в тексте"
    headers = {"Authorization": f"Bearer {token}"}
    data = {
        "text": text,
        "lang": "ru-RU",
        "voice": "oksana",
        "format": "oggopus"
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(YANDEX_TTS_URL, headers=headers, data=data)
        return response.content


async def recognize(audio_bytes: bytes, token: str) -> str:
    "Распознает речь в тексте"
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient() as client:
        response = await client.post(YANDEX_STT_URL, headers=headers, content=audio_bytes)
        return response.json().get("result", "")