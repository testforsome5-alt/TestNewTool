# AI Idea Validator для стартапов

Теперь в репозитории есть не только продуктовый бриф, но и рабочий backend MVP.

## Что реализовано в коде

- FastAPI API для анализа идеи.
- Генерация структурированного отчёта (market, ICP, competitors, roadmap, risks).
- Сохранение истории анализов в SQLite.
- Получение списка прошлых идей пользователя.
- Получение конкретного отчёта по `idea_id`.

## API endpoints

- `GET /health` — проверка работоспособности.
- `POST /ideas/analyze` — анализ идеи и сохранение в историю.
- `GET /ideas/history/{user_id}` — история идей пользователя.
- `GET /ideas/{idea_id}` — детальный просмотр одного отчёта.

## Пример запроса

```json
{
  "user_id": "founder-1",
  "title": "AI Idea Validator",
  "idea": "Сервис для быстрой валидации стартап-идей с roadmap и историей.",
  "region": "Global"
}
```

## Локальный запуск

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

После запуска: `http://127.0.0.1:8000/docs`

## Тесты

```bash
pytest
```

## Product brief (кратко)

### Формат продукта
- Вводишь идею.
- Получаешь анализ: рынок, ICP, конкуренты, MVP roadmap.
- История идей хранится в аккаунте.

### Монетизация
- Free: 3 анализа/месяц.
- Pro: безлимит + экспорт.
- Team: общий workspace.

### MVP roadmap
1. Week 1: customer discovery.
2. Week 2–3: landing + fake door.
3. Week 4–5: core MVP loop.
4. Week 6: pricing и первый пилот.
