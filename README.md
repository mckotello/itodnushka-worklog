# ITоднушка Worklog

Сервис для учёта рабочего времени, задач и рентабельности проектов.

Проект предназначен для независимого разработчика или небольшой IT-студии: помогает вести проекты, отслеживать затраченное время и оценивать стоимость работы относительно бюджета.

## Возможности

### Проекты

* создание проектов;
* редактирование проектов;
* удаление проектов;
* указание клиента, бюджета, почасовой ставки и дедлайна;
* статусы проекта: активный, завершённый, архивный;
* расчёт затраченного времени;
* расчёт стоимости работы;
* расчёт остатка бюджета;
* процент использования бюджета;
* изоляция проектов между пользователями.

### Задачи

* создание задач внутри проекта;
* просмотр списка задач;
* изменение статуса задачи;
* удаление задач;
* привязка рабочего времени к конкретной задаче.

### Учёт времени

* ручное создание временных записей через API;
* запуск и остановка таймера;
* привязка таймера к задаче;
* история рабочего времени;
* удаление временных записей;
* расчёт продолжительности работы;
* расчёт стоимости затраченного времени.

### Dashboard

Главная страница показывает:

* количество проектов;
* количество активных проектов;
* общее затраченное время;
* общую стоимость работы;
* общий бюджет проектов;
* процент использования бюджета;
* список проектов.

### Авторизация и безопасность

* регистрация пользователей;
* JWT-аутентификация;
* Argon2 для хранения паролей;
* проверка владельца проекта;
* проверка доступа к задачам;
* проверка доступа к временным записям;
* изоляция данных между пользователями;
* валидация входных данных через Pydantic.

### Web-интерфейс

Проект содержит рабочий web-интерфейс на HTML, CSS и JavaScript.

Через интерфейс доступны:

* регистрация и вход;
* dashboard;
* создание и редактирование проектов;
* управление задачами;
* запуск и остановка таймера;
* история рабочего времени;
* удаление временных записей;
* просмотр финансовых показателей проекта.

Отдельный frontend-фреймворк не используется: интерфейс работает непосредственно через FastAPI и REST API.

## Стек

### Backend

* Python 3.13
* FastAPI
* Pydantic
* SQLAlchemy 2
* PostgreSQL 17
* Alembic
* PyJWT
* Argon2

### Frontend

* HTML5
* CSS3
* JavaScript
* Fetch API
* LocalStorage для JWT

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
├── static/
│   ├── index.html
│   ├── style.css
│   └── app.js
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
README.md
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

После запуска приложение будет доступно по адресу:

```text
http://localhost:8000
```

Web-интерфейс:

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

Web-интерфейс сохраняет JWT в LocalStorage и автоматически добавляет его к API-запросам.

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

## Пример сценария

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

Например:

```text
Почасовая ставка: 3000 ₽
Затрачено: 1.5 часа
```

Стоимость работы:

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
* запрет доступа к чужим проектам;
* валидация входных данных через Pydantic.

Все операции с проектами выполняются в контексте текущего пользователя.

Например, пользователь не может получить проект другого пользователя, даже если знает его `project_id`.

Для активного таймера используется ограничение на уровне PostgreSQL, которое не позволяет создать несколько активных таймеров для одного проекта одновременно.

## Тестирование

Запустить все тесты:

```bash
docker compose exec app pytest -v
```

Тестовый набор покрывает:

* регистрацию и авторизацию;
* повторную регистрацию;
* неверный пароль;
* JWT;
* валидацию email;
* CRUD проектов;
* изоляцию проектов;
* пагинацию проектов;
* dashboard;
* расчёт рентабельности;
* валидацию денежных значений;
* CRUD задач;
* изоляцию задач;
* валидацию задач;
* пагинацию задач;
* создание временных записей;
* таймер;
* расчёт стоимости;
* привязку времени к задачам;
* пагинацию временных записей;
* удаление временных записей;
* изоляцию временных записей;
* обработку несуществующих ресурсов;
* проверку авторизации.

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

Таким образом, изменения автоматически проверяются в CI.

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
* [x] Web-интерфейс
* [x] Создание и редактирование проектов
* [x] Управление задачами
* [x] Таймер
* [x] История рабочего времени
* [x] Удаление временных записей

### Возможные следующие этапы

* [ ] Redis
* [ ] Celery для фоновых задач
* [ ] Production deployment
* [ ] отчёты по проектам
* [ ] экспорт данных
* [ ] уведомления
* [ ] расширенная аналитика
* [ ] анализ фактической и плановой рентабельности

## Цель проекта

Проект демонстрирует практическую разработку полноценного web-сервиса:

* проектирование REST API;
* работу с PostgreSQL;
* асинхронный SQLAlchemy;
* JWT-аутентификацию;
* безопасное хранение паролей;
* миграции базы данных;
* валидацию данных;
* контроль доступа;
* пагинацию;
* расчёт финансовых показателей;
* тестирование API;
* CI;
* контейнеризацию;
* интеграцию backend и frontend.

Проект также может использоваться как внутренний инструмент для учёта времени и рентабельности IT-проектов.
