<!-- v. 0.0.9 -->
# FastAPI-EdgeDB-DDD v0.0.8

## Описание
FastAPI-EdgeDB-DDD - Проект на основе :book: "Паттерны разработки на Python: TDD, DDD и событийно-ориентированная архитектура" (Персиваль Гарри и Грегори Боб).
Паттерны репозитория, тонких вью, менеджеров контекста и сообщений, позволяют выстроить событийно-управляемую модель.
Разделение приложения на слои, позволяет уменьшить гранулярность тестирования, т.к. каждый слой легко покрыть быстрыми юниттестами.
Цель не просто воспроизвести проект из учебника, а протестировать насколько такая архитектура позволяет  легко заменять компоненты системы - фреймворк и базу данных.

## Технологии
- FastAPI: Быстрый асинхронный веб-фреймворк для Python.
- EdgeDB: База данных с выразительным синтаксисом запросов.
- Redis Pub/Sub: Механизм Publisher - Subscribers в Redis.
- Pytest: Мощный фреймворк для написания и запуска тестов.
- Docker: Контейнеризация для удобного развертывания.

## Преимущества
- Освоение паттернов DDD и чистой архитектуры.
- Архитектура позволила легко заменить Flask на FastAPI, а связку Postgres + SQLAlchemy на EdgeDB.
- Легкость тестирования и интеграции благодаря разделению приложения на слои.
- Шаблонная структура проекта и подходит для создания своих проектов.

## Сложности:
- Подходы из учебника задают высокую константу кода в виде бойлерплейта, что может быть не рациональным для небольших задач.
- Возможные проблемы интеграции.
- Необходимость изучить системы доставки сообщений(Kafka, RabbitMQ)

## Рост:
Улучшение навыков проектирования.
Применение паттернов в других проектах.
Опыт интеграции новых библиотек и приложений.

# Установка и Запуск:  
_Представлены команды для системы Ubuntu_
## Инициализация проекта
1. Клонируйте проект:
```sh
   git clone https://github.com/Gen121/Fastapi-EdgeDB-DDD.git
   cd Fastapi-EdgeDB-DDD
```
2. Установите зависимости:
```sh
   python3 -m venv venv && source venv/bin/activate
   pip install -r requirements.txt
   pip install -e src/
```
3. Создайте файл .env:
```sh
 cp env.example .env
```
Эта команда копирует содержимое файла env.example в новый файл .env в корневой директории, по соседству c каталогом src

<!--Если вы используете операционную систему Windows и командную строку cmd, то команда будет выглядеть так:

batch
Copy code
copy .env.example .env -->


4. Запустите команду Make:
```sh
    make all 
```
В процессе запуска будет собрано несколько контейнеров Docker и после запуска выполнено тестирование
<!-- TODO: В процессе запуска будет собран {Здесь расписать поднятие докер-контейнеров} -->
## Запуск тестов

```sh
make test
# or, to run individual test types
make unit
make integration
make e2e
# or, if you have a local virtualenv
make up
pytest tests/unit
pytest tests/integration
pytest tests/e2e
```


## Образец .env файла
```.env
# .env.example

# Отключение создания .pyc файлов и буферизации вывода
PYTHONDONTWRITEBYTECODE=1
PYTHONUNBUFFERED=1

APP_NAME="edgedb"
NETWORK_NAME="local_dbs_network"

# EdgeDB 
DB_USER_NAME="edgedb"
DB_NAME="edgedb"
DB_TEST_NAME="edgedb"
DB_ROOT_PASSWORD="edgedb"
DB_HOSTNAME="edgedb"
DB_PORT=5656

## Имена томов для данных и схем БД
DB_VOLUME_DATA_NAME="${DB_CONTAINER_NAME}_data"
DB_VOLUME_SCHEMA_NAME="${DB_CONTAINER_NAME}_schema"

DB_CONTAINER_NAME="${APP_NAME}"

# API-сервер
API_HOST="localhost"
API_PORT=5005

# Redis
REDIS_HOST="redis"
REDIS_PORT=6379

# Хост отправки электронной почты
EMAIL_HOST="mailhog"
```