# these will speed up builds, for docker compose >= 1.25
export COMPOSE_DOCKER_CLI_BUILD=1
export DOCKER_BUILDKIT=1

all: down build up test

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down --remove-orphans

test: up
	docker compose run --rm --no-deps --entrypoint=pytest api -s /tests/unit /tests/integration /tests/e2e

unit-tests:
	docker compose run --rm --no-deps --entrypoint=pytest api /tests/unit

integration-tests: up
	docker compose run --rm --no-deps --entrypoint=pytest api /tests/integration

e2e-tests: up
	docker compose run --rm --no-deps --entrypoint=pytest api -s /tests/e2e

logs:
	docker compose logs api | tail -100

black:
	black -l 86 $$(find * -name '*.py')