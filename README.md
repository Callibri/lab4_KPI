# Лабораторна робота 4. Синхронна та асинхронна комунікація

![tests](https://github.com/Callibri/lab4/actions/workflows/tests.yml/badge.svg)

Розширення лабораторної 3. Допоміжний компонент Audit (журнал бізнес-дій) лежить в `src/boxoffice/audit` зі своїм контрактом. Після кожної команди система повідомляє компонент двома способами, режим обирається змінною `COMMUNICATION_MODE`.

| Значення | Поведінка |
|---|---|
| `sync` | обробник команди викликає Audit напряму через інтерфейс у тому самому потоці |
| `async` (за замовчуванням) | обробник публікує подію в Event Bus, Audit обробляє її окремо |
| `none` | без побічних операцій |

Додаткова змінна `AUDIT_DELAY_MS` додає затримку в Audit, щоб було видно різницю в часі відповіді.

## Встановлення

Потрібен Python 3.11 або новіший.

Windows (PowerShell):

```
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Linux / macOS:

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Запуск

Windows (PowerShell):

```
$env:COMMUNICATION_MODE="async"
uvicorn boxoffice.main:app --app-dir src --reload
```

Linux / macOS:

```
COMMUNICATION_MODE=async uvicorn boxoffice.main:app --app-dir src --reload
```

Перегляд журналу: `GET /audit` (потрібен токен), фільтр `?entity_type=report`.

## Тести та вимірювання

```
pytest -v
python scripts/benchmark_communication.py
```

Скрипт вимірює час відповіді й поведінку при збої Audit для режимів `sync` та `async`. Результати використані в `docs/analysis/lab4.md`.

Тести:
- `tests/application/test_side_effects.py` обидва способи, збої, вимоги до подій;
- `tests/infrastructure/test_event_bus.py` шина подій;
- `tests/audit` компонент Audit;
- `tests/integration/test_communication.py` обидва режими з базою даних.

## Події

`UserRegistered`, `MovieCreated`, `MovieUpdated`, `MovieDeleted`, `ReportAdded`, `ReportCorrected`, `ReportDeleted`. Події незмінні, мають `event_id` і достатньо даних для обробки без додаткових запитів. Повторна доставка події не створює дубль запису в Audit.

## Документи

- `docs/analysis/lab4.md` порівняльний аналіз;
