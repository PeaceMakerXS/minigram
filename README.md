# Minigram
Микросервис для работы авторизации в рамках проекта Minigram. Реализует регистрацию, подтверждение email, вход, обновление токенов и управление сессиями.

## Оглавление

- [Структура проекта](#структура-проекта)
- [Технологии](#технологии)
- [Системные требования](#системные-требования)
  - [Запуск через Docker](#запуск-через-docker-требования)
  - [Запуск без Docker](#запуск-без-docker-требования)
- [Переменные окружения](#переменные-окружения)
- [Запуск](#запуск)
  - [Через Docker](#через-docker)
  - [Без Docker (локально)](#без-docker-локально)
- [Миграции](#миграции)
- [API эндпойнты](#api-эндпойнты)
- [Модели данных](#модели-данных)
- [Примеры запросов (curl)](#примеры-запросов-curl)

---

## Структура проекта

```
minigram/
├── docker-compose.yml          # Оркестрация всех сервисов
├── docker-compose-dev.yml      # Конфигурация для разработки
├── .env                        # Переменные окружения
├── .env.example               # Пример переменных окружения
├── .gitignore                 # Git ignore файл
├── Dockerfile                 # Dockerfile для auth сервиса
├── docker-entrypoint.sh       # Скрипт запуска контейнера
├── alembic.ini               # Конфигурация Alembic
├── requirements.txt          # Python зависимости
├── app/                      # Основное приложение
│   ├── __init__.py
│   ├── app.py                # Точка входа FastAPI
│   ├── settings.py           # Конфигурация (pydantic-settings)
│   ├── db/
│   │   ├── __init__.py
│   │   ├── database.py       # Async engine + session factory
│   │   ├── column_annotations.py
│   │   └── repository_base.py
│   ├── main/
│   │   ├── __init__.py
│   │   ├── cache.py          # Redis-обёртка для кодов подтверждения
│   │   ├── dependencies.py   # FastAPI-зависимости (auth middleware)
│   │   ├── models.py         # SQLAlchemy-модели (User, Session)
│   │   ├── repositories.py   # Репозитории (UserRepository, SessionRepository)
│   │   ├── routers.py        # Эндпойнты аутентификации
│   │   ├── schema.py         # Pydantic-схемы запросов/ответов
│   │   └── service.py        # Бизнес-логика аутентификации
│   └── migrations/           # Миграции Alembic
└── README.md
```

---

## Технологии

- **Python 3.11**
- **FastAPI** — веб-фреймворк
- **SQLAlchemy 2.0 (async)** — ORM
- **asyncpg** — драйвер PostgreSQL
- **Redis** — хранение кодов подтверждения email
- **PyJWT** — генерация и проверка JWT-токенов
- **argon2-cffi** — хэширование паролей
- **pydantic-settings** — конфигурация через .env

---

## Системные требования

### Запуск через Docker (требования)

| Инструмент       | Минимальная версия | Назначение                        |
|------------------|--------------------|-----------------------------------|
| **Docker**       | 24.0+              | Контейнеризация сервисов          |
| **Docker Compose** | 2.20+ (plugin)   | Оркестрация контейнеров           |

> Всё остальное (Python, PostgreSQL, Redis) поднимается автоматически внутри контейнеров.

### Запуск без Docker (требования)

> Предполагается, что **PostgreSQL** и **Redis** уже запущены и доступны локально.

| Инструмент          | Минимальная версия | Назначение                        |
|---------------------|--------------------|-----------------------------------|
| **Python**          | 3.11+              | Интерпретатор                     |
| **pip**             | 23.0+              | Менеджер пакетов                  |
| **PostgreSQL**      | 14+                | База данных (должна быть запущена)|
| **Redis**           | 7+                 | Кэш для кодов (должен быть запущен)|

---

## Переменные окружения

Скопируйте `.env.example` в `.env` и заполните значения:

```bash
cp .env.example .env
```

| Переменная               | По умолчанию            | Описание                              |
|--------------------------|-------------------------|---------------------------------------|
| `POSTGRES_HOST`          | `localhost`             | Хост PostgreSQL                       |
| `POSTGRES_PORT`          | `5432`                  | Порт PostgreSQL                       |
| `POSTGRES_DB`            | `auth`                  | Имя базы данных                       |
| `POSTGRES_USER`          | `postgres`              | Пользователь БД                       |
| `POSTGRES_PASSWORD`      | `postgres`              | Пароль БД                             |
| `REDIS_HOST`             | `localhost`             | Хост Redis                            |
| `REDIS_PORT`             | `6379`                  | Порт Redis                            |
| `REDIS_PASSWORD`         | `""`                    | Пароль Redis                          |
| `REDIS_DB`               | `0`                     | Номер БД Redis                        |
| `JWT_ACCESS_SECRET`      | `jwt-secret`            | Секрет для подписи JWT                |
| `JWT_ACCESS_TTL_SECONDS` | `900`                   | Время жизни access token (сек.)       |
| `JWT_REFRESH_TTL_SECONDS`| `2592000`               | Время жизни refresh token (сек.)      |
| `EMAIL_CODE_TTL_SECONDS` | `900`                   | Время жизни кода подтверждения (сек.) |
| `CORS_ALLOWED_ORIGINS`   | `http://localhost:3000` | Разрешённые CORS-источники            |

---

## Запуск

### Через Docker

```bash
# Из корня minigram
docker compose up --build
```

Swagger UI доступен по адресу `http://localhost:8081/docs`.

### Без Docker (локально)

> Убедитесь, что PostgreSQL и Redis уже запущены и доступны. Переменные окружения заданы в `.env`.

```bash
# 1. Создать и активировать виртуальное окружение
python3 -m venv .venv
source .venv/bin/activate

# 2. Установить зависимости
pip install -r requirements.txt

# 3. Создать базу данных (если ещё не создана)
psql -U postgres -c "CREATE DATABASE auth;"

# 4. Применить миграции
alembic upgrade head

# 5. Запустить сервер
uvicorn app.app:app --host 0.0.0.0 --port 8081 --reload
```

Swagger UI доступен по адресу `http://localhost:8081/docs`.

---

## Миграции

- Миграции управляются через **Alembic**
- После старта приложения все миграции из `app/migrations/versions` применяются автоматически (в Docker)

Если нужно создать и применить миграцию вручную:

**В Docker:**
```bash
docker compose exec auth bash
alembic revision --autogenerate -m "init"
alembic upgrade head
```

**Локально:**
```bash
alembic revision --autogenerate -m "init"
alembic upgrade head
```

---

## API эндпойнты

| Метод   | Путь                            | Аутентификация | Описание                                     |
|---------|---------------------------------|----------------|----------------------------------------------|
| POST    | `/api/v1/auth/register`         | —              | Регистрация нового пользователя              |
| POST    | `/api/v1/auth/register/confirm` | —              | Подтверждение email по 6-значному коду       |
| POST    | `/api/v1/auth/login`            | —              | Вход и получение пары access/refresh токенов |
| POST    | `/api/v1/auth/refresh`          | —              | Обновление пары токенов по refresh token     |
| POST    | `/api/v1/auth/logout`           | Bearer token   | Удаление сессии (refresh token)              |
| GET     | `/api/v1/auth/sessions`         | Bearer token   | Список активных сессий пользователя          |
| DELETE  | `/api/v1/auth/sessions/{id}`    | Bearer token   | Отзыв конкретной сессии                      |
| GET     | `/healthz`                      | —              | Health-check                                 |

---

## Модели данных

#### User
| Поле         | Тип          | Описание                          |
|--------------|--------------|-----------------------------------|
| id           | UUID (PK)    | Уникальный идентификатор          |
| email        | VARCHAR(255) | Email (уникальный)                |
| password     | VARCHAR(255) | argon2-хэш пароля                 |
| is_verified  | BOOLEAN      | Подтверждён ли email              |
| created_at   | TIMESTAMPTZ  | Дата создания                     |
| updated_at   | TIMESTAMPTZ  | Дата обновления                   |

#### Session
| Поле          | Тип          | Описание                          |
|---------------|--------------|-----------------------------------|
| id            | UUID (PK)    | Уникальный идентификатор          |
| user_id       | UUID (FK)    | Ссылка на User                    |
| refresh_token | VARCHAR(512) | Refresh token (уникальный)        |
| user_agent    | TEXT         | User-Agent клиента                |
| ip            | VARCHAR(45)  | IP-адрес клиента                  |
| expires_at    | TIMESTAMPTZ  | Срок действия сессии              |
| created_at    | TIMESTAMPTZ  | Дата создания                     |

---

## Примеры запросов (curl)

> Базовый URL: `http://localhost:8081`

### Регистрация

**Запрос:**
```bash
curl -s -X POST http://localhost:8081/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "secret123"}'
```

**Ответ `201 Created`:**
```json
{
  "message": "registration successful, check your email",
  "confirm_code": "482910"
}
```

---

### Подтверждение email

**Запрос:**
```bash
curl -s -X POST http://localhost:8081/api/v1/auth/register/confirm \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "code": "482910"}'
```

**Ответ `200 OK`:**
```json
{
  "message": "email confirmed"
}
```

---

### Вход

**Запрос:**
```bash
curl -s -X POST http://localhost:8081/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "user@example.com", "password": "secret123"}'
```

**Ответ `200 OK`:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 900,
  "token_type": "Bearer"
}
```

---

### Обновление токенов

**Запрос:**
```bash
curl -s -X POST http://localhost:8081/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}'
```

**Ответ `200 OK`:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_in": 900,
  "token_type": "Bearer"
}
```

---

### Выход (logout)

**Запрос:**
```bash
curl -s -X POST http://localhost:8081/api/v1/auth/logout \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -d '{"refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."}'
```

**Ответ `200 OK`:**
```json
{
  "message": "logged out"
}
```

---

### Список активных сессий

**Запрос:**
```bash
curl -s -X GET http://localhost:8081/api/v1/auth/sessions \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Ответ `200 OK`:**
```json
{
  "sessions": [
    {
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
      "ip": "127.0.0.1",
      "expires_at": "2026-04-15T10:00:00+00:00",
      "created_at": "2026-03-16T10:00:00+00:00"
    }
  ]
}
```

---

### Отзыв конкретной сессии

**Запрос:**
```bash
curl -s -X DELETE http://localhost:8081/api/v1/auth/sessions/3fa85f64-5717-4562-b3fc-2c963f66afa6 \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**Ответ `200 OK`:**
```json
{
  "message": "session revoked"
}
```

---

### Health-check

**Запрос:**
```bash
curl -s http://localhost:8081/healthz
```

**Ответ `200 OK`:**
```json
{
  "status": "ok"
}
```
