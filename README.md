# Yandex Hackathon Bot

Telegram бот для проведения опросов с интеграцией Яндекс Форм.

## Архитектура

Проект состоит из пяти основных компонентов:

- **Bot** - Telegram бот на aiogram 3.x
- **Backend** - Django REST API для управления пользователями и опросами
- **Frontend** - Веб-интерфейс для управления опросами
- **Database** - PostgreSQL для хранения данных
- **Infra** - Инфраструктурные конфигурации и скрипты

## Структура проекта

```
├── bot/                    # Telegram бот
│   ├── handlers/          # Обработчики команд и состояний
│   ├── services.py        # Сервисы для работы с API
│   ├── config.py          # Конфигурация
│   ├── main.py            # Точка входа
│   └── requirements.txt   # Python зависимости бота
├── backend/               # Django API
│   ├── surveys/           # Приложение для опросов
│   │   ├── models.py      # Модели данных
│   │   ├── views.py       # API endpoints
│   │   ├── serializers.py # Сериализаторы
│   │   └── urls.py        # URL маршруты
│   ├── backend/           # Настройки Django
│   ├── requirements.txt   # Python зависимости бэкенда
│   └── Dockerfile         # Docker образ бэкенда
├── frontend/              # Веб-интерфейс
│   └── Dockerfile         # Docker образ фронтенда
├── infra/                 # Инфраструктура
│   ├── conf.d             # Конфигурация Nginx
├── docker-compose.yml     # Docker Compose конфигурация
├── .env.example           # Пример переменных окружения
└── README.md              # Документация проекта
```

## Модели данных

### User
- `tg_nickname` - Telegram username (уникальный)
- `name` - Имя
- `surname` - Фамилия
- `age` - Возраст
- `gender` - Пол (M/F/O)

### Survey
- `external_id` - ID формы в Яндекс Формах
- `title` - Название опроса
- `description` - Описание
- `questions` - Список вопросов (JSON)

### SurveyResponse
- `survey` - Ссылка на опрос
- `user` - Ссылка на пользователя (опционально)
- `answers` - Ответы пользователя (JSON)
- `telegram_user_id` - ID пользователя в Telegram
- `telegram_username` - Username в Telegram

## API Endpoints

### Пользователи
- `POST /api/users/register/` - Регистрация пользователя
- `GET /api/users/by-nickname/{nickname}/` - Получить пользователя по username

### Опросы
- `POST /api/surveys/import/` - Импорт опроса из Яндекс Форм
- `GET /api/surveys/test-yandex/` - Тест подключения к Яндекс Формам
- `POST /api/surveys/{id}/submit/` - Отправка ответов на опрос

## Запуск проекта

### Требования
- Docker и Docker Compose
- Python 3.9+

### Переменные окружения

Создайте файл `.env` в корне проекта:

```env
# Bot
TG_TOKEN=your_telegram_bot_token

# Database
DB_NAME=hackathon_bot
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=localhost
DB_PORT=5432

# Backend
SECRET_KEY=your_secret_key
USER_SERVICE_BASE_URL=http://backend:8000
USER_SERVICE_TIMEOUT=5.0

# External API
EXTERNAL_API_URL=your_external_api_url

# Yandex Forms (опционально)
YANDEX_CLIENT_ID=your_yandex_client_id
YANDEX_CLIENT_SECRET=your_yandex_client_secret
```

### Запуск

```bash
# Запуск всех сервисов
docker-compose up -d

# Просмотр логов
docker-compose logs -f

# Остановка
docker-compose down
```

## Разработка

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows

pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

### Bot

```bash
cd bot
python -m venv venv
source venv/bin/activate  # Linux/Mac
# или
venv\Scripts\activate     # Windows

pip install -r requirements.txt
python main.py
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

### Infra

```bash
# Настройка мониторинга
cd infra/monitoring
docker-compose up -d

# Развертывание в продакшн
cd infra/scripts
./deploy.sh
```

## Функциональность

### Регистрация пользователей
1. Пользователь отправляет `/start`
2. Бот проверяет, зарегистрирован ли пользователь
3. Если нет - запрашивает имя, фамилию, возраст, пол
4. Сохраняет данные в базе через API

### Прохождение опросов
1. Пользователь вводит номер анкеты
2. Бот загружает вопросы из API
3. Поочередно задает вопросы
4. Сохраняет ответы через API

## TODO

- [ ] Интеграция с Яндекс Формами API
- [ ] Админка для управления опросами
- [ ] Статистика и аналитика
- [ ] Экспорт результатов
- [ ] Уведомления о новых опросах
- [ ] Многоязычность

## Технологии

- **Bot**: aiogram 3.x, asyncio, httpx
- **Backend**: Django REST Framework
- **Frontend**: React, TypeScript, Vite
- **Database**: PostgreSQL
- **Infrastructure**: Docker, Docker Compose, Nginx
- **Monitoring**: Prometheus, Grafana, ELK Stack