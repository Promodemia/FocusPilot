# Contributing to FocusPilot

## Быстрый старт для разработки

### 1. Клонировать и установить зависимости

```bash
git clone https://github.com/Promodemia/FocusPilot.git
cd FocusPilot

# Backend
cd FocusPilot_core
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate.bat
pip install -r requirements.txt
pip install pytest httpx    # dev-зависимости для тестов

# Frontend
cd ../gui
npm install
```

### 2. Запуск тестов

```bash
# Из корня проекта
cd FocusPilot_core
pytest tests/ -v
```

### 3. Запуск в dev-режиме

```bash
# Terminal 1
python FocusPilot_core/main.py

# Terminal 2
cd gui && npm run tauri:dev
```

---

## Структура тестов

```
FocusPilot_core/
└── tests/
    ├── test_api.py        # тесты FastAPI эндпоинтов
    ├── test_models.py     # тесты ML классификатора
    └── test_database.py   # тесты слоя БД
```

Пример теста:
```python
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health():
    response = client.get("/health")
    assert response.status_code == 200
    assert "aw_available" in response.json()
```

---

## Стиль кода

- Python: PEP 8, форматтер `black`
- Rust: `cargo fmt` перед коммитом
- Коммиты: `feat: ...`, `fix: ...`, `docs: ...`, `refactor: ...`

---

## Как предложить изменение

1. Форкни репозиторий
2. Создай ветку: `git checkout -b feat/my-feature`
3. Сделай изменения + тесты
4. Открой Pull Request с описанием что и зачем изменено
