# Book Tracker API

🔗 **Живой API:** https://book-tracker-api-frnm.onrender.com/api/books/
📖 **Swagger-документация:** https://book-tracker-api-frnm.onrender.com/api/docs/

> Бесплатный тариф Render «засыпает» после периода неактивности — первый
> запрос после простоя может занять 30–60 секунд, дальше работает быстро.

Личный трекер прочитанных книг: каталог книг, статусы («хочу прочитать» /
«читаю» / «прочитано» / «бросил(а)»), оценки, заметки, теги, поиск и фильтры.

## Стек

- Django 5 + Django REST Framework
- PostgreSQL
- JWT-аутентификация (`djangorestframework-simplejwt`)
- Фильтрация (`django-filter`)
- Автогенерируемая OpenAPI/Swagger-документация (`drf-spectacular`)
- Тесты: `pytest` + `pytest-django`
- Линтер: `ruff`
- Продакшен: `gunicorn` + `whitenoise`, деплой на Render

## Структура проекта

```
config/
├── settings/
│   ├── base.py   ← общие настройки для всех окружений
│   ├── dev.py    ← локальная разработка (используется по умолчанию)
│   └── prod.py   ← продакшен: DEBUG=False, обязательные env-переменные,
│                    security-заголовки
├── urls.py
├── wsgi.py / asgi.py
books/
├── models.py, serializers.py, views.py, filters.py, admin.py, urls.py
└── tests/
    ├── conftest.py   ← общие фикстуры (пользователи, книги, теги)
    └── test_*.py
```

Окружение выбирается переменной `DJANGO_SETTINGS_MODULE` (по умолчанию —
`config.settings.dev`). Для продакшен-деплоя выставь
`DJANGO_SETTINGS_MODULE=config.settings.prod` и обязательно задай
`SECRET_KEY` и `ALLOWED_HOSTS` в переменных окружения — без них prod-конфиг
осознанно откажется стартовать, а не тихо заработает в небезопасном режиме.
Базу данных прод-конфиг берёт из `DATABASE_URL` (стандарт Render/Railway),
если она задана, иначе — из отдельных `DB_*` переменных.

## Запуск локально

```bash
python -m venv venv
source venv/bin/activate       # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env           # и подставить свои значения
# создать БД в Postgres: createdb booktracker

python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

Swagger UI локально: `http://127.0.0.1:8000/api/docs/`

## Тесты

```bash
pytest
```

## Линтер

```bash
ruff check .        # проверка
ruff check . --fix  # автофикс того, что чинится автоматически
```

## Основные эндпоинты

Полное описание с интерактивной проверкой прямо в браузере — в Swagger UI
(`/api/docs/`). Кратко:

| Метод | Путь | Описание |
|---|---|---|
| POST | `/api/auth/register/` | Регистрация |
| POST | `/api/auth/login/` | Получить access/refresh токены |
| POST | `/api/auth/refresh/` | Обновить access-токен |
| GET/POST | `/api/books/` | Список книг / добавить книгу |
| GET/PUT/PATCH/DELETE | `/api/books/{id}/` | Работа с конкретной книгой |
| GET | `/api/books/?search=...&genre=...&tag=...` | Поиск и фильтры |
| GET/POST | `/api/my-books/` | Личная библиотека текущего пользователя |
| GET | `/api/my-books/{id}/` | Детали конкретной записи |
| PATCH | `/api/my-books/{id}/` | Изменить статус/оценку/заметки |
| DELETE | `/api/my-books/{id}/` | Удалить запись из своей библиотеки |
| GET | `/api/my-books/?status=...` | Фильтр по статусу чтения |
| GET | `/api/my-books/stats/` | Статистика: всего книг, разбивка по статусам, средняя оценка, количество оценённых книг |
| GET/POST | `/api/tags/` | Теги |
| GET/PUT/DELETE | `/api/tags/{id}/` | Работа с конкретным тегом |
| GET | `/api/schema/` | Сырая OpenAPI-схема |
| GET | `/api/docs/` | Swagger UI |

## Модель данных

```
Book (title, author, genre, year_published, cover_url) ──┬── ManyToMany ── Tag
                                                            │
User ── ForeignKey ── UserBook (status, rating, notes) ────┘ ForeignKey ── Book
```

Ограничение: одна пара «пользователь + книга» — не более одной записи
(`unique_user_book`), оценку можно поставить только книге со статусом
«прочитано».

## Дальнейшие шаги (по мере роста проекта)

- Пагинация уже включена (по 20 записей), можно донастроить под себя
- Кэширование статистики (Redis) при росте нагрузки