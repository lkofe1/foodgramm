# Проект Foodgram

![Foodgram Workflow](https://github.com/lkofe1/foodgramm/actions/workflows/main.yml/badge.svg) 

## Описание
**Foodgram** — это онлайн-сервис, через которое пользователи могут публиковать свои рецепты, подписываться на публикации других пользователей, добавлять понравившиеся рецепты в список «Избранное», а также скачивать список продуктов для приготовления выбранных блюд.

### Основные функции приложения:
* *Управление профилем:* Регистрация и аутентификация пользователей на базе токенов (Djoser).

* *Кулинарная книга:* Создание, редактирование и просмотр рецептов с указанием ингредиентов, времени готовки и пошаговой инструкции.

* *Интерактивность:* Система подписок на авторов и добавление рецептов в «Избранное».

* *Список покупок:* Автоматическое формирование сводного списка продуктов для выбранных рецептов с возможностью скачивания в формате .txt.

* *Автоматизация (CI/CD):* Автоматическая проверка линтером, сборка свежих Docker-образов и деплой на удаленный сервер при каждом пуше в ветку master.

---

## Стек технологий

* *Backend:* Python 3.12, Django, Django REST Framework, Djoser, Gunicorn

* *Frontend:* React, HTML5, CSS3

* *Database:* PostgreSQL 14

* *Infrastructure:* Docker, Docker Compose, Nginx, Linux (Ubuntu)

* *CI/CD:* GitHub Actions, Telegram API

---

## Инструкция по локальному развертыванию

1. **Клонируйте репозиторий и перейдите в него:**

```bash
git clone https://github.com/lkofe1/foodgramm
cd foodgram
```

2. Настройте переменные окружения:
    В корневой директории проекта создайте файл .env (шаблон см. ниже).

3. Запустите проект в Docker-контейнерах:

```bash
sudo docker compose up -d --build
```

4. Выполните миграции бэкенда и загрузите базу ингредиентов:

```bash
sudo docker compose exec backend python manage.py migrate
sudo docker compose exec backend python manage.py load_ingredients
```

5. Соберите статичные файлы приложения:

```bash
sudo docker compose exec backend python manage.py collectstatic --no-input
```

# Теперь проект будет доступен локально по адресу: http://localhost

# Настройка окружения (Шаблон файла .env)
     Для успешного запуска проекта как локально, так и на сервере, создайте файл .env в корневой директории со следующими переменными:

SECRET_KEY=ваш_секретный_ключ_django
DEBUG=False
ALLOWED_HOSTS=127.0.0.1,localhost,edagramm.ydns.eu

DB_ENGINE=django.db.backends.postgresql
POSTGRES_DB=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=ваш_пароль_к_базе
DB_HOST=db
DB_PORT=5432

# Настройка CI/CD (GitHub Actions)
    Процесс автоматизации разбит на следующие этапы:

1. Тестирование: Проверка кода линтером flake8.

2. Сборка и публикация: Сборка Docker-образов для бэкенда, фронтенда и Nginx (gateway) и их отправка на Docker Hub.

3. Деплой: Автоматическое подключение к удаленному серверу по SSH, загрузка обновленных образов, применение миграций, сбор статики и перезапуск контейнеров.


Автор
lkofe1 — Разработка бэкенд-логики, проектирование API, контейнеризация приложения, настройка веб-сервера Nginx и конфигурация CI/CD пайплайна.