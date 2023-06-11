# Проект по учебнику Персиваль - Паттерны разработки на Python (DDD)

## Описание

Проект должен воспроизвестиу чебный материал из учебника, использя при этом другой веб фреймвок и базу данных.

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
python3.8 -m venv .venv && source .venv/bin/activate # or however you like to create virtualenvs

# for chapter 1
pip install pytest 

# for chapter 2
pip install pytest sqlalchemy

# for chapter 4+5
pip install requirements.txt

# for chapter 6+
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


