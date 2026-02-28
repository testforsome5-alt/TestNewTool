# AI Idea Validator для стартапов

Теперь это рабочий MVP c аккаунтами, ролями и web UI.

## Что реализовано

- Аккаунты (`/auth/register`, `/auth/login`) с ролями `user` и `admin`.
- Авторизация API через заголовок `X-API-Token`.
- Анализ идеи: `POST /ideas/analyze`.
- История идей пользователя: `GET /ideas/history/{user_id}`.
- Просмотр конкретного отчёта: `GET /ideas/{idea_id}`.
- Список подключенных моделей: `GET /models`.
- Preview промпта под модель: `POST /prompts/preview`.
- User UI: `GET /ui/user/{user_id}`.
- Admin UI: `GET /ui/admin`.

## Архитектура данных

SQLite таблицы:
- `users`: email, hash пароля, role, api_token.
- `reports`: user_id, идея, модель, JSON-отчёт, timestamp.

## Пример сценария

1. Зарегистрировать пользователя:

```bash
curl -X POST http://127.0.0.1:8000/auth/register \
  -H 'Content-Type: application/json' \
  -d '{"email":"founder@example.com","password":"secret123","role":"user"}'
```

2. Сделать анализ:

```bash
curl -X POST http://127.0.0.1:8000/ideas/analyze \
  -H 'Content-Type: application/json' \
  -H 'X-API-Token: <TOKEN>' \
  -d '{
    "user_id":"1",
    "title":"AI Idea Validator",
    "idea":"Сервис анализирует стартап-идею и формирует roadmap.",
    "region":"EU",
    "model":"gpt-4o-mini"
  }'
```

3. Открыть UI:
- Пользователь: `http://127.0.0.1:8000/ui/user/1`
- Админ: `http://127.0.0.1:8000/ui/admin`

## Локальный запуск

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Swagger: `http://127.0.0.1:8000/docs`

## Тесты

```bash
pytest -q
```

## Что дальше

- Подключить реальные провайдеры LLM вместо детерминированного генератора.
- Добавить reset/revoke токенов, JWT и rate limit.
- Сделать полноценную frontend-панель (React/Vue) вместо server-side HTML.
