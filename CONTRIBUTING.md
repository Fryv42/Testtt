# Contributing Guidelines

## Ветвление (Git Flow)

| Префикс | Назначение | Пример |
|---------|------------|--------|
| `feature/` | Новый функционал | `feature/quiz-creation` |
| `fix/` | Исправление багов | `fix/login-error` |
| `docs/` | Документация | `docs/readme-update` |
| `chore/` | Настройки, конфиги | `chore/lint-config` |
| `refactor/` | Рефакторинг | `refactor/models` |

## Формат коммитов
Используем Convention Commits:
`type(#issue_id): description`

### Типы коммитов:
- `feat` — новый функционал
- `fix` — исправление багов
- `docs` — документация
- `chore` — настройки, конфиги
- `refactor` — рефакторинг кода
- `test` — добавление тестов

### Примеры:
- `feat(#12): добавить регистрацию пользователя`
- `fix(#15): исправить ошибку валидации пароля`
- `docs(#0): обновить README`
- `refactor(#20): оптимизировать запросы к БД`