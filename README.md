# AI Idea Validator (Production-ready MVP skeleton)

Проект переработан архитектурно: логика разделена по слоям, добавлены чат-история, таблицы/графики в ответах, auth UI и публичные страницы для запуска.

## Архитектура

- `app/main.py` — bootstrap приложения, роутеры, error-handling policy.
- `app/core/db.py` — SQLite и инициализация схемы.
- `app/models/schemas.py` — Pydantic-схемы DTO.
- `app/services/` — бизнес-логика (`auth_service`, `report_service`, `chat_service`).
- `app/routers/` — transport-слой API/UI (`auth`, `ideas`, `chat`, `pages`).
- `app/prompts.py` — конфиг поддерживаемых моделей и prompt templates.

## Что реализовано

### 1) Accounts + login
- Регистрация/логин по email+password: `POST /auth/register`, `POST /auth/login`.
- Role-based access: `user` / `admin`.
- API auth через `X-API-Token`.

### 2) Social login providers (MVP flow)
- `GET /auth/oauth/{provider}/start` (`google`, `github`, `apple`, `microsoft`).
- `GET /auth/oauth/{provider}/callback?email=...` (демо callback для локальной среды).

### 3) Idea validator
- `POST /ideas/analyze` — сохраняет отчёт в БД.
- `GET /ideas/history/{user_id}` — история идей.
- `GET /ideas/{idea_id}` — детальная карточка.

### 4) Chat + history
- `POST /chat/message` — сообщение пользователя + ответ ассистента.
- `GET /chat/history/{user_id}` — полная история чата.

### 5) Графики и таблицы в ответах
- В `IdeaReport` добавлены `tables` и `charts` для отображения в UI.

### 6) Public pages and policies
- `/`, `/pricing`, `/privacy`, `/terms`, `/cookies`, `/security`.
- Кастомная 404 страница для web-трафика.

### 7) UI pages
- `/auth/register/page`, `/auth/login/page`.
- `/ui/user/{user_id}`.
- `/ui/admin`.

## Запуск

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

- Swagger: `http://127.0.0.1:8000/docs`

## Тесты

```bash
pytest -q
```
