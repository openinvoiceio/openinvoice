.DEFAULT_GOAL := all

.PHONY: install
install:
	uv install

.PHONY: lint
lint:
	uv run ruff check

.PHONY: typecheck
typecheck:
	uv run mypy

.PHONY: format
format:
	uv run ruff format && uv run ruff check --fix

.PHONY: test
test:
	uv run pytest

.PHONY: openapi
openapi:
	uv run manage.py spectacular --file ../dashboard/openapi.yaml --format openapi

.PHONY: migrations
migrations:
	uv run manage.py makemigrations

.PHONY: all
all: lint format typecheck test