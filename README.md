# Проект по учебнику Персиваль - Паттерны разработки на Python (DDD)

## Описание

Цель проекта  воспроизвести проект из учебника, протестировав насколько удобно заменять благодаря использованию чистой архитектуры компоненты системы, а именно  фреймворк и базу данных.

## Технологии
FastAPI, EdgeDB, Pytest, Docker


## Building the containers

_(this is only required from chapter 3 onwards)_

```sh
make build
make up
# or
make all # builds, brings containers up, runs tests
```

## Creating a local virtualenv (optional)

```sh
python3 -m venv venv && source venv/bin/activate # or however you like to create virtualenvs

pip install requirements.txt
pip install -e src/
```

<!-- TODO: use a make pipinstall command -->


## Running the tests

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


