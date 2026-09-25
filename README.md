# ITоднушка Worklog

Сервис для учёта рабочего времени, задач и рентабельности проектов.

Проект разработан как backend-сервис для независимого разработчика или небольшой IT-студии.

## Возможности

* регистрация и авторизация пользователей;
* JWT-аутентификация;
* безопасное хранение паролей через Argon2;
* создание и управление проектами;
* привязка проектов к пользователям;
* задачи внутри проектов;
* учёт рабочего времени;
* ручное создание временных записей;
* запуск и остановка таймера;
* привязка времени к задачам;
* расчёт стоимости затраченного времени;
* расчёт остатка бюджета проекта;
* dashboard с общей статистикой;
* пагинация проектов, задач и временных записей;
* изоляция данных между пользователями;
* валидация входных данных;
* автоматические тесты API;
* CI через GitHub Actions.

## Стек

### Backend

* Python 3.13
* FastAPI
* Pydantic
* SQLAlchemy 2
* PostgreSQL 17
* Alembic
* JWT
* Argon2

### Testing

* pytest
* pytest-asyncio
* HTTPX

### Infrastructure

* Docker
* Docker Compose
* GitHub Actions

## Архитектура

```text
app/
├── api/
│   ├── auth.py
│   ├── projects.py
│   ├── tasks.py
│   ├── time_entries.py
│   └── dependencies.py
│
├── models/
│   ├── base.py
│   ├── user.py
│   ├── project.py
│   ├── task.py
│   └── time_entry.py
│
├── schemas/
│   ├── auth.py
│   ├── project.py
│   ├── task.py
│   └── time_entry.py
│
├── services/
│   ├── project_access_service.py
│   ├── project_service.py
│   ├── task_service.py
│   └── time_entry_service.py
│
├── auth.py
├── security.py
├── config.py
├── database.py
└── main.py

alembic/
├── versions/
└── env.py

tests/
├── conftest.py
├── test_auth.py
├── test_project_service.py
├── test_projects.py
├── test_task_service.py
├── test_tasks.py
├── test_time_entry_service.py
└── test_time_entries.py

.github/
└── workflows/
    └── tests.yml

docker-compose.yml
Dockerfile
pyproject.toml
alembic.ini
```

## Запуск

### 1. Клонирование проекта

```bash
git clone <repository-url>
cd itodnushka-worklog
```

### 2. Создание `.env`

Создай файл `.env`:

```env
DATABASE_URL=postgresql+asyncpg://worklog:worklog@postgres:5432/worklog
JWT_SECRET_KEY=<your-secret-key>
```

`JWT_SECRET_KEY` должен содержать случайное секретное значение и не должен попадать в Git.

### 3. Запуск Docker Compose

```bash
docker compose up --build
```

После запуска API будет доступен по адресу:

```text
http://localhost:8000
```

Swagger UI:

```text
http://localhost:8000/docs
```

ReDoc:

```text
http://localhost:8000/redoc
```

## Миграции

Применить миграции:

```bash
docker compose exec app alembic upgrade head
```

Создать новую миграцию:

```bash
docker compose exec app alembic revision --autogenerate -m "description"
```

## Проверка приложения

Проверка API:

```text
GET /health
```

Ответ:

```json
{
  "status": "ok"
}
```

Проверка подключения к PostgreSQL:

```text
GET /health/db
```

Ответ:

```json
{
  "status": "ok",
  "database": 1
}
```

## Авторизация

Регистрация:

```http
POST /auth/register
```

Пример:

```json
{
  "email": "user@example.com",
  "password": "test12345"
}
```

Ответ:

```json
{
  "access_token": "...",
  "token_type": "bearer"
}
```

Полученный JWT передаётся в последующих запросах:

```http
Authorization: Bearer <access_token>
```

## Основные API

### Projects

```text
POST   /projects/
GET    /projects/
GET    /projects/{project_id}
PUT    /projects/{project_id}
DELETE /projects/{project_id}

GET    /projects/{project_id}/summary
GET    /projects/dashboard
```

Список проектов поддерживает пагинацию:

```text
GET /projects/?page=1&limit=20
```

Параметры:

* `page` — номер страницы, начиная с 1;
* `limit` — количество элементов на странице, от 1 до 100.

Ответ:

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "limit": 20,
  "pages": 0
}
```

### Tasks

```text
POST   /projects/{project_id}/tasks/
GET    /projects/{project_id}/tasks/
PUT    /projects/{project_id}/tasks/{task_id}
DELETE /projects/{project_id}/tasks/{task_id}
```

Список задач поддерживает пагинацию:

```text
GET /projects/{project_id}/tasks/?page=1&limit=20
```

Ответ имеет тот же формат:

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "limit": 20,
  "pages": 0
}
```

### Time entries

```text
POST   /projects/{project_id}/time-entries/
GET    /projects/{project_id}/time-entries/
DELETE /projects/{project_id}/time-entries/{time_entry_id}

POST   /projects/{project_id}/time-entries/start
POST   /projects/{project_id}/time-entries/stop

GET    /projects/{project_id}/time-entries/cost
```

Список временных записей поддерживает пагинацию:

```text
GET /projects/{project_id}/time-entries/?page=1&limit=20
```

Ответ:

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "limit": 20,
  "pages": 0
}
```

## Пример сценария

Типичный сценарий работы:

```text
Регистрация
    ↓
Получение JWT
    ↓
Создание проекта
    ↓
Создание задачи
    ↓
Запуск таймера
    ↓
Работа над задачей
    ↓
Остановка таймера
    ↓
Расчёт затраченного времени
    ↓
Расчёт стоимости
    ↓
Контроль бюджета проекта
```

Например, если:

```text
Почасовая ставка: 3000 ₽
Затрачено: 1.5 часа
```

стоимость работы составит:

```text
4500 ₽
```

## Безопасность

API использует несколько уровней защиты:

* JWT для аутентификации;
* Argon2 для хеширования паролей;
* проверка существования пользователя;
* проверка владельца проекта;
* проверка владельца задачи через проект;
* проверка владельца временной записи;
* запрет доступа пользователя к чужим проектам;
* валидация входных данных через Pydantic.

Все операции с проектами выполняются в контексте текущего пользователя.

Например, пользователь не может получить проект другого пользователя даже если знает его `project_id`.

Для активного таймера также используется ограничение на уровне PostgreSQL, не позволяющее создать несколько активных таймеров для одного проекта одновременно.

## Тестирование

Запустить все тесты:

```bash
docker compose exec app pytest -v
```

Текущий набор содержит **81 автоматический тест**.

Покрываются:

* регистрация;
* повторная регистрация;
* авторизация;
* неверный пароль;
* невалидный JWT;
* истёкший JWT;
* валидация email;
* CRUD проектов;
* изоляция проектов;
* пагинация проектов;
* dashboard;
* расчёт рентабельности;
* валидация денежных значений;
* CRUD задач;
* изоляция задач;
* валидация задач;
* пагинация задач;
* создание временных записей;
* таймер;
* расчёт стоимости;
* привязка времени к задачам;
* пагинация временных записей;
* удаление временных записей;
* изоляция временных записей;
* обработка несуществующих ресурсов;
* проверка авторизации.

## CI

Для проекта настроен GitHub Actions.

При `push` в `main` и при создании Pull Request запускаются:

```text
Checkout
    ↓
Python 3.13
    ↓
PostgreSQL 17
    ↓
Установка зависимостей
    ↓
Alembic migrations
    ↓
pytest
```

Таким образом, изменения проверяются автоматически до попадания в основную ветку.

## База данных

Основные сущности:

```text
User
 │
 └── Project
      │
      ├── Task
      │
      └── TimeEntry
```

Связи:

```text
User 1 ─── N Project
Project 1 ─── N Task
Project 1 ─── N TimeEntry
Task 1 ─── N TimeEntry
```

При удалении проекта связанные задачи и временные записи удаляются каскадно.

При удалении задачи связанная временная запись сохраняется, но её `task_id` становится `NULL`.

## Текущий статус

### Реализовано

* [x] FastAPI backend
* [x] PostgreSQL
* [x] SQLAlchemy 2
* [x] Alembic
* [x] JWT authentication
* [x] Argon2 password hashing
* [x] Projects API
* [x] Tasks API
* [x] Time tracking API
* [x] Project profitability
* [x] Dashboard
* [x] Ownership isolation
* [x] API validation
* [x] Pagination
* [x] Automated tests
* [x] Docker Compose
* [x] GitHub Actions CI

### Планируется

* [ ] Web-интерфейс
* [ ] Redis
* [ ] Celery для фоновых задач
* [ ] Production deployment
* [ ] отчёты по проектам
* [ ] экспорт данных
* [ ] уведомления
* [ ] аналитика по фактической и плановой рентабельности

## Цель проекта

Проект демонстрирует практическую разработку backend-сервиса:

* проектирование REST API;
* работу с PostgreSQL;
* асинхронный SQLAlchemy;
* JWT-аутентификацию;
* миграции базы данных;
* валидацию данных;
* контроль доступа;
* пагинацию;
* тестирование API;
* CI;
* контейнеризацию.

Проект также может использоваться как внутренний инструмент для учёта времени и рентабельности IT-проектов.
