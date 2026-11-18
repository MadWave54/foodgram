# Фудграм — продуктовый помощник

Сервис публикации рецептов: регистрация по email, токены, аватары,
подписки на авторов, избранное, список покупок с суммированием продуктов
и постоянные короткие ссылки. Готовый React-клиент из стартового
репозитория https://github.com/AlexBryzga/foodgram-st работает с Django REST API.

## Быстрый запуск в Windows

Нужен запущенный Docker Desktop с Linux-контейнерами.
Откройте PowerShell в папке проекта:

```powershell
cd infra
Copy-Item .env.example .env
docker compose up -d --build
docker compose exec backend python manage.py seed_demo
```

Первый запуск скачивает образы и собирает React; это может занять несколько минут.
Миграции и сбор статических файлов Django выполняются автоматически.
Повторное выполнение `seed_demo` не дублирует рецепты и не меняет пароли.

- Сайт: http://localhost:8080
- Админка: http://localhost:8080/admin/
- Спецификация API: http://localhost:8080/api/docs/
- API: http://localhost:8080/api/

Учебные аккаунты (вход по **email**, общий пароль `Foodgram-Demo-2026`):

| Email | Роль |
| --- | --- |
| admin@foodgram.local | Суперпользователь, доступ в админку |
| matvey@foodgram.local | Автор рецептов |
| anna@foodgram.local | Автор рецептов |

Демо содержит восемь рецептов с условными иллюстрациями и справочник
ингредиентов из задания. Для собственных рецептов загружайте фотографии.

## Команды управления

Выполняются из `infra`:

```powershell
docker compose ps
docker compose logs --tail 100 backend nginx
docker compose exec backend python manage.py load_ingredients
docker compose exec backend python manage.py createsuperuser
docker compose exec backend python manage.py test api
docker compose stop
docker compose up -d
```

Данные PostgreSQL, изображения, статика и сборка клиента хранятся в отдельных
Docker volumes. `docker compose stop` их сохраняет.
Порт задаётся переменной `FOODGRAM_PORT` в `infra/.env`.

## Проверки

Интеграционные тесты проверяют суммирование покупок и изоляцию пользователей,
права автора, атомарное отклонение повторяющихся ингредиентов, подписки,
короткие ссылки, вход и отзыв токенов.

```powershell
docker compose exec backend python manage.py test api
docker compose exec backend python manage.py makemigrations --check --dry-run
```

Коллекция Postman из задания запускается из корня проекта:

```powershell
npx.cmd --yes newman run postman_collection/foodgram.postman_collection.json --env-var baseUrl=http://localhost:8080
```

Перед повторным прогоном удалите только три тестовые учётные записи
`vasya.ivanov`, `second-user`, `third-user-username` через админку:
коллекция использует фиксированные email. Демо-аккаунты удалять не нужно.
В исходной коллекции исправлена одна проверка: сравнение префикса ингредиента
теперь регистронезависимое, как требует задание. Остальные запросы и проверки сохранены.
Отчёт локального прогона находится в `verification/postman-results.json`.

## Структура

- `backend/users` — пользователи, аватары и подписки;
- `backend/recipes` — рецепты, ингредиенты, избранное и покупки;
- `backend/api` — сериализаторы, права, пагинация, обработчики API и тесты;
- `frontend` — готовое React-приложение;
- `infra` — Docker Compose, PostgreSQL и Nginx;
- `data` — справочник ингредиентов;
- `docs` — OpenAPI и ReDoc;
- `.github/workflows/foodgram.yml` — проверки, сборка образов и развёртывание.

Технологии: Python 3.12, Django 5.2, DRF, Djoser, PostgreSQL 16,
Gunicorn, Nginx, React 17, Docker Compose.
SQLite предусмотрена для тестирования Python без Docker; основной запуск — PostgreSQL.

## GitHub Actions и сервер

Для публикации создайте собственный GitHub-репозиторий и загрузите проект.
В Settings → Secrets and variables → Actions добавьте:

- variable `DOCKERHUB_USERNAME` — логин Docker Hub;
- secret `DOCKERHUB_TOKEN` — токен Docker Hub;
- secrets `HOST`, `SSH_USER`, `SSH_KEY` — адрес сервера, пользователь и SSH-ключ.

Каждый push в main/master запускает тесты и сборку клиента; при настроенном
Docker Hub публикует два образа. Развёртывание запускается через Run workflow
с включённым `deploy`.

На сервере с Docker разместите проект в `/opt/foodgram`, настройте `infra/.env`:
задайте собственные `SECRET_KEY`, пароль PostgreSQL, `DOCKERHUB_USERNAME`,
домен в `ALLOWED_HOSTS` и полный адрес сайта в `CSRF_TRUSTED_ORIGINS`.
Для обычного HTTP используйте `FOODGRAM_PORT=80`; HTTPS настройте на внешнем прокси.
Первый запуск: `docker compose up -d --no-build`, затем
`docker compose exec backend python manage.py load_ingredients`
и `docker compose exec backend python manage.py createsuperuser`.

Публикация в GitHub/Docker Hub и развёртывание на внешнем сервере требуют
учётных записей и реквизитов владельца; локальный проект работает независимо от них.
