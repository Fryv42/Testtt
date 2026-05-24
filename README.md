# Сервис для проведения квизов (Django)

## Описание
Онлайн-платформа для создания и проведения викторин с синхронным участием.

## Стек технологий
- **Backend:** Django 4.2 + Django REST Framework
- **Database:** SQLite (dev) / PostgreSQL (prod)
- **WebSocket:** Django Channels
- **Frontend:** HTML5 + Bootstrap 5 + JavaScript
- **API-документация:** OpenAPI 3 + Swagger UI (`drf-spectacular`)

## Требования
- Python 3.10+
- PostgreSQL 14+
- Redis 6+
- Gunicorn/Daphne
- Nginx

## OpenAPI / Swagger

После установки зависимостей и миграций запустите сервер и откройте в браузере:

| URL | Назначение |
|-----|------------|
| `/api/docs/` | Swagger UI (интерактивная документация) |
| `/api/schema/` | Сырая OpenAPI 3 схема (YAML по умолчанию) |

### Генерация `schema.yml` вручную

Из корня репозитория:

```bash
python manage.py spectacular --file schema.yml
```

Проверка схемы без записи файла:

```bash
python manage.py spectacular --validate --fail-on-warn
```

В CI при каждом пайплайне схема валидируется (job `openapi`) и собирается для артефактов; job `docs` встраивает актуальный `schema.yml` в Sphinx.

## Генерация документации (Sphinx)

Сборка HTML включает автоматическую генерацию `schema.yml` и встраивание схемы в раздел **OpenAPI** документации:

```bash
pip install -r requirements.txt
cp .env.example .env
cd docs
make html
```

Результат: `docs/_build/html/index.html`.

## Тестирование

### Backend (pytest)

```bash
pip install -r requirements.txt
cp .env.example .env
mkdir -p logs
python manage.py migrate
pytest --cov=app --cov-report=term-missing
```

### Frontend (Jest, каталог `static/js`)

```bash
npm install
npm test
npm run test:coverage
```

### Качество кода (Pylint)

```bash
pylint app sapere_aude --rcfile=.pylintrc
```

В GitLab CI задачи `lint`, `test`, `openapi` и `docs` запускаются автоматически.

## Деплой на сервер

Сервер: `188.127.254.20`, каталог `/home/site1/app/sapere-aude`.

Подробно: [docs/DEPLOY.md](docs/DEPLOY.md).

Кратко:

1. Один раз: `deploy/server-bootstrap.sh` на VPS.
2. В GitLab CI/CD -> Variables: `SSH_PRIVATE_KEY` (приватный ключ для SSH).
3. Push в `main` -> job `deploy:production` обновит код и перезапустит сервис.

## Установка

```bash
# Клонировать репозиторий
git clone <repository-url>
cd sapere-aude

# Создать виртуальное окружение
python -m venv venv
source venv/bin/activate

# Установить зависимости
pip install -r requirements.txt

# Скопировать .env.example
cp .env.example .env
# Отредактировать .env с production-значениями

# Применить миграции
python manage.py migrate

# Собрать статику
python manage.py collectstatic --noinput

# Запустить через Daphne (для WebSocket)
daphne -b 0.0.0.0 -p 8000 sapere_aude.asgi:application
```

## WebSocket API

Для интерактивного взаимодействия с викториной в реальном времени используется протокол WebSocket.

### Эндпоинт
http://localhost:8000/

ws://<host>:8000/ws/quiz/<session_code>/
- `<session_code>` – уникальный код сессии (строка, например `abc123`).
