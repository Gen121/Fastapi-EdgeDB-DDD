# check docker compose version
DOCKER_COMPOSE := $(shell command -v docker-compose)
ifeq ($(DOCKER_COMPOSE),)
DOCKER_COMPOSE := docker compose
endif

# optimisation for builds, docker compose >= 1.25
export COMPOSE_DOCKER_CLI_BUILD=1
export DOCKER_BUILDKIT=1

all: down build up test

build:
	$(DOCKER_COMPOSE) build

up:
	$(DOCKER_COMPOSE) up -d

down:
	$(DOCKER_COMPOSE) down --remove-orphans

test: up
	$(DOCKER_COMPOSE) run --rm --no-deps --entrypoint=pytest api -s /tests/unit /tests/integration /tests/e2e

unit-tests:
	$(DOCKER_COMPOSE) run --rm --no-deps --entrypoint=pytest api /tests/unit

integration-tests: up
	$(DOCKER_COMPOSE) run --rm --no-deps --entrypoint=pytest api /tests/integration

e2e-tests: up
	$(DOCKER_COMPOSE) run --rm --no-deps --entrypoint=pytest api -s /tests/e2e

logs:
	$(DOCKER_COMPOSE) logs api | tail -100

black:
	black -l 86 $$(find * -name '*.py')