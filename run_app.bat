@echo off
setlocal

:: Установка переменных среды
set COMPOSE_DOCKER_CLI_BUILD=1
set DOCKER_BUILDKIT=1

:all
call :down
call :build
call :up
call :test
goto :eof

:build
docker-compose build
goto :eof

:up
docker-compose up -d
goto :eof

:down
docker-compose down --remove-orphans
goto :eof

:test
call :up
call :unit-tests
call :integration-tests
call :e2e-tests
goto :eof

:unit-tests
docker-compose run --rm --no-deps --entrypoint=pytest api /tests/unit
goto :eof

:integration-tests
call :up
docker-compose run --rm --no-deps --entrypoint=pytest api /tests/integration
goto :eof

:e2e-tests
call :up
docker-compose run --rm --no-deps --entrypoint=pytest api /tests/e2e
goto :eof

:logs
docker-compose logs api | tail -100
goto :eof

:black
black -l 86 %cd%\*.py

:end
endlocal