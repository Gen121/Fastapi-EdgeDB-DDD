<!-- v. 0.0.9 -->
# FastAPI-EdgeDB-DDD v0.0.8

## Description

|<span style="font-weight:normal;">Description: FastAPI-EdgeDB-DDD is a project based on "Architecture Patterns with Python: Enabling Test-Driven Development, Domain-Driven Design, and Event-Driven Microservices" (by Persival Harry and Gregory Bob). The repository, thin view, context managers, and messagebus pattern allow for building an Event-driven architecture. The partition of the application into layers helps reduce the granularity of testing, as each layer can be easily covered with quick unit tests. The goal is not only to replicate the project from the textbook but also to test how such architecture allows for easy replacement of system components - frameworks and databases.</span>  | <img src="https://encrypted-tbn2.gstatic.com/images?q=tbn:ANd9GcTyDEHpipE4vZO8w16A770h6nk33TeTcu57MB_zW4QXPAtOhx-d" alt="Альтернативный текст" style="max-width:300px;"> |
|:---------------|----------------:|


### 🧬 Full Project Diagram

<pre>
  ┌─────────────────────────┐       ┌──────────────────────────────┐  
┌─► <a href="https://github.com/redis/redis">External Message Broker</a> │       │             WEB              ◄───┐
│ └─────┬───────────────────┘       └───────────────────────────┬──┘   │  
│       │                                                       │      │  
│ ┌─────▼─────────┐                        ────              ┌──▼──┐   │  
│ │ <a href="src/allocation/adapters/redis_eventpublisher.py">Eventconsumer</a> ├──────────────────────►/    \◄────────────┤ <a href="src/allocation/app/main.py">API</a> │   │  
│ └─────┬─────────┘                      /      \            └───┬─┘   │
│       │                               /        \               │     │
│       │                              / <a href="src/allocation/bootstrap.py">Bootstrap</a>\              │     │
│       │                              \          /              │     │
│       │                               \        /               │     │
│       │       ┌─────────────────────────      /                │     │
│       │       │                         \────/                 │     │
│       │       │                                                │     │
│       │       │       ┌────────────────────────────────────────┘     │
│       │       │       │                                              │
│    ---│-------│-------│-------------------------------------------   │
│    -  │       │       │                                          -   │
│    -  │       │       │      ┌────────────┐                      -   │
│    -  │       │       │      │ ---------- │                      -   │
│    - ┌▼───────▼───────▼┐     ├────────────┤     ┌──────────────┐ -   │
│    - │    <a href="src/allocation/services/messagebus.py">Messagebus</a>   ├────►│  <a href="src/allocation/services/handlers.py">Handlers</a>  ├────►│ <a href="src/allocation/services/unit_of_work.py">unit_of_work</a> │ -   │
│    - └─────────────────┘     ├────────────┤     └───────┬──────┘ -   │
│    -                         │ ---------- │             │        -   │
│    -                         └────────────┘             │        -   │
│    -  <a href="src/allocation/services">Services</a>                                          │        -   │
│    -----------------------------------------------------│---------   │
│                                                         │            │
│                                    ┌────────────────────┘            │
│                                    │                                 │
│    --------------------------------│------------------------------   │
│    -                               │                             -   │
│    - ┌────────────────┐   ┌────────▼────────┐  ┌───────────────┐ -   │
└──────┤ <a href="src/allocation/adapters/redis_eventpublisher.py">Eventpublisher</a> │   │   <a href="src/allocation/repositories/repository.py">Repositories</a>  │  │  <a href="src/allocation/adapters/notifications.py">Notifications</a>├─────┘
     - └────────────────┘   └─────┬───────┬───┘  └───────────────┘ -
     -                            │       │                        -
     -  <a href="src/allocation/adapters">Adaptorstions</a>             │       │                        -
     -----------------------------│-------│-------------------------
                                  │       │
         ┌─────────────┐          │       │        ┌─────────────┐
         │             │          │       │        │             │
         │ <a href="src/allocation/domain/model.py">Domain area</a> ◄──────────┘       └────────►    <a href="https://github.com/edgedb/edgedb">EdgeDB</a>   │
         │             │                           │             │
         └─────────────┘                           └─────────────┘
</pre>



## Technology
- FastAPI: A fast asynchronous web framework for Python.
- EdgeDB: A database with expressive query syntax.
- Redis Pub/Sub: Publisher-Subscribers mechanism in Redis.
- Pytest: A powerful framework for writing and running tests.
- Docker: Containerization for convenient deployment.

## Advantages
- Mastery of DDD and clean architecture patterns.
- The architecture allowed for easy replacement of Flask with FastAPI and Postgres + SQLAlchemy with EdgeDB.
- Ease of testing and integration due to the separation of the application into layers.
- Template project structure suitable for creating your own projects.

## Challenges:
- Approaches from the textbook introduce a significant amount of boilerplate code, which might not be rational for small tasks.
- Potential integration issues.
- The need to learn message delivery systems (Kafka, RabbitMQ).

## Help Needed

|I've encountered an issue with testing parallel transactions that I can't resolve on my own. The original testing code uses the threading module: Original Test Code [tests/integration/test_uow.py - original](https://github.com/cosmicpython/code/blob/734df09afc65ba43c851271def147c70ac3c3b98/tests/integration/test_uow.py#L94C8-L94C8) As I use an asynchronous framework, I've modified it: Asynchronous Test Code [tests/integration/test_uow.py - asynchrony](https://github.com/Gen121/Fastapi-EdgeDB-DDD/blob/073ee2dc5d7189ee638881648a22a6a81e7119af/tests/integration/test_uow.py#L95) During testing, I encounter the exception ```edgedb.errors.TransactionSerializationError: could not serialize access due to concurrent update``` Tests are only stopped by a keyboard interrupt (KeyboardInterrupt). I suspect my problem stems from the fact that I'm just starting to learn what asynchronous code is. Maybe I'm not opening and closing the asynchronous transaction context manager correctly:: Async Unit of Work context manager [src/allocation/services/unit_of_work.py](https://github.com/Gen121/Fastapi-EdgeDB-DDD/blob/Change_DB_for_EdgeDB/src/allocation/services/unit_of_work.py) If anyone could assist, I'd be grateful. Feel free to reach out via comments, [Telegram](https://t.me/CheEugene), or [Twitter](https://twitter.com/chelnok1190).|
|:-------------------------------:|
## Growth:
Enhancement of design skills.
Application of patterns in other projects.
Experience in integrating new libraries and applications.

# Installation and Running:
_Commands are provided for both Ubuntu and Windows systems_
<details>
  <summary>Ubuntu</summary>
  
## Project Initialization
1. Clone the project:
```sh
   git clone https://github.com/Gen121/Fastapi-EdgeDB-DDD.git
   cd Fastapi-EdgeDB-DDD
```
2. Install dependencies:
```sh
   python3 -m venv venv && source venv/bin/activate
   pip install -r requirements.txt
   pip install -e src/
```
3. Create a .env file:
```sh
 cp env.example .env
```
This command copies the contents of the env.example file into a new .env file in the root directory, next to the src directory.

4. Run the Make command:
```sh
    make all 
```
During the execution, several Docker containers will be built, and after the launch, testing will be performed.

## Run tests
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

</details>


<details>
  <summary>Windows</summary>

## Project Initialization
1. Clone the project:
```cmd
   git clone https://github.com/Gen121/Fastapi-EdgeDB-DDD.git
   cd Fastapi-EdgeDB-DDD
```
2. Install dependencies:
```cmd
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   pip install -e src\
```
3. Create a .env file:
```cmd
   copy env.example .env

```
This command copies the contents of the env.example file into a new .env file in the root directory, next to the src directory.

4. Run the .bat script to build and start the container:
```cmd
   run_app.bat call :all 
```
During the execution, several Docker containers will be built, and after the launch, testing will be performed.

## Run tests
```cmd
   run_app.bat call :test

# or, to run individual test types
   run_app.bat call :unit-tests
   run_app.bat call :integration-tests
   run_app.bat call:e2e-tests

# or, if you have a local virtualenv
   run_app.bat call :up
   pytest tests/unit
   pytest tests/integration
   pytest tests/e2e
```

</details>


## Sample .env file
```.env
# .env.example

# Disabling .pyc file creation and output buffering
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

## Volume names for database data and schemas
DB_VOLUME_DATA_NAME="${DB_CONTAINER_NAME}_data"
DB_VOLUME_SCHEMA_NAME="${DB_CONTAINER_NAME}_schema"

DB_CONTAINER_NAME="${APP_NAME}"

# API-server
API_HOST="localhost"
API_PORT=5005

# Redis
REDIS_HOST="redis"
REDIS_PORT=6379

# Email sending host
EMAIL_HOST="mailhog"
```

<details>
  <summary>[на русском]</summary>

## Описание
|<span style="font-weight:normal;">Описание: FastAPI-EdgeDB-DDD - Проект на основе "Паттерны разработки на Python: TDD, DDD и событийно-ориентированная архитектура" (Персиваль Гарри и Грегори Боб).Паттерны репозитория, тонких вью, менеджеров контекста и сообщений, позволяют выстроить событийно-управляемую модель. Разделение приложения на слои, позволяет уменьшить гранулярность тестирования, т.к. каждый слой легко покрыть быстрыми юниттестами. Цель не просто воспроизвести проект из учебника, а протестировать насколько такая архитектура позволяет  легко заменять компоненты системы - фреймворк и базу данных.</span>  | <img src="https://static.insales-cdn.com/images/products/1/5229/453669997/44611468.jpg" alt="Альтернативный текст" style="max-width:300px;"> |
|:---------------|----------------:|


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
_Представлены команды для ос Ubuntu и Windows_

<details>
  <summary>Ubuntu</summary>
  
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


4. Запустите команду Make:
```sh
   make all 
```
В процессе запуска будет собрано несколько контейнеров Docker и после запуска выполнено тестирование

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

</details>


<details>
  <summary>Windows</summary>

## Инициализация проекта

1. Клонируйте проект:
```cmd
   git clone https://github.com/Gen121/Fastapi-EdgeDB-DDD.git
   cd Fastapi-EdgeDB-DDD
```

2. Установите зависимости:
Создание и активация виртуальной среды:
```cmd
   python -m venv venv
   venv\Scripts\activate
   pip install -r requirements.txt
   pip install -e src\
```

3. Создайте файл .env:
```cmd
   copy env.example .env
```
Эта команда копирует содержимое файла env.example в новый файл .env
 в корневой директории, по соседству c каталогом src

4. Запустите сценарий сборки и запуска контейнера:
```cmd
   run_app.bat call :all 
```
В процессе будет собрано несколько контейнеров Docker,
 после их запуска выполнено тестирование сервиса

## Запуск тестов
```cmd
   run_app.bat call :test

   # или для запуска отдельных типов тестов
   run_app.bat call :unit-tests
   run_app.bat call :integration-tests
   run_app.bat call:e2e-tests

   # или, если у вас есть virtualenv
   run_app.bat call :up
   pytest tests/unit
   pytest tests/integration
   pytest tests/e2e
```

</details>


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
</details>
