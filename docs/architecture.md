# Архитектура сервиса проведения квизов

## Обзор компонентов
Система построена на Django с использованием Django REST Framework для API
и Django Channels для WebSocket соединений.

## Диаграмма компонентов
```mermaid
C4Context
    title Контекстная диаграмма системы "Сервис квизов"

    Person(organizer, "Организатор", "Создает квизы, управляет сессией")
    Person(participant, "Участник", "Подключается по коду, отвечает на вопросы")

    System_Boundary(system, "Сервис квизов (Django)") {
        System(frontend, "Frontend", "Веб-интерфейс", "HTML/JS/Bootstrap")
        System(backend, "Backend (Django)", "API, логика игры", "Python/Django")
        SystemDb(database, "PostgreSQL/SQLite", "Хранение данных", "SQL")
    }

    Rel(organizer, frontend, "Управление квизами", "HTTPS")
    Rel(participant, frontend, "Прохождение квиза", "HTTPS")
    Rel(frontend, backend, "REST API + WebSocket", "HTTP/WSS")
    Rel(backend, database, "Чтение/Запись", "SQL")