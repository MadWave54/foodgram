# Результаты локальной проверки

Дата: 18 ноября 2026.

- Docker Compose: PostgreSQL, Django/Gunicorn, React build, Nginx.
- Postman/Newman: 139 запросов, 198 проверок, 0 ошибок.
- Django integration tests в контейнере с PostgreSQL: 6 passed.
- Django integration tests с локальной SQLite: 6 passed.
- Ruff: All checks passed.
- Главная, список рецептов, документация, OpenAPI и вход в админку: HTTP 200.
- В браузере проверены список из шести рецептов, вход по email и кнопка покупок.

Полный отчёт: `postman-results.json`.
В коллекции исправлено сравнение префикса ингредиента: регистр больше
не влияет на результат проверки, согласно требованиям задания.
