# Yandex Hackathon Bot

Система опросов с Telegram ботом и Django бекендом.

## Запуск через Docker

1. Скопируйте файл с примером переменных окружения:
```bash
cp env.example .env
```

2. Отредактируйте `.env` файл, заменив значения на ваши:
```bash
# Django
SECRET_KEY=django-insecure-change-this-in-production

# PostgreSQL Database
DB_NAME=hackathon_bot
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432

# Яндекс Формы API
YANDEX_CLIENT_ID=c3ccafbf46824d3b85748cbdb869aa52
YANDEX_CLIENT_SECRET=081482918074440a87501a0de2a57543

# Telegram Bot
TG_TOKEN=your_telegram_bot_token_here
```

3. Запустите все сервисы:
```bash
docker-compose up --build
```

4. Или только бекенд:
```bash
docker-compose up backend
```

## API Endpoints

- `POST /api/surveys/import` - Импорт анкеты из Яндекс Форм
- `POST /api/surveys/{id}/submit` - Отправка ответов на анкету

## Структура проекта

- `backend/` - Django REST API
- `bot/` - Telegram бот на aiogram
- `frontend/` - Веб-интерфейс (пока не готов)
- `infra/` - Инфраструктура