# Hacktrek WebCrawler — common developer commands.
#
#   make install        install backend + dev + frontend deps
#   make test           run the backend pytest suite (offline)
#   make run-api        start the FastAPI backend with reload
#   make run-frontend   start the Vite dev server
#   make lint           lint the frontend
#   make build-frontend build the production frontend bundle
#   make docker-build   build the backend Docker image
#   make docker-up      run the stack with docker compose
#
# PY points at the interpreter. Override on Windows if needed, e.g.:
#   make test PY=venv/Scripts/python.exe

PY ?= python
PIP ?= $(PY) -m pip

.PHONY: help install install-backend install-frontend test run-api run-frontend \
        lint build-frontend docker-build docker-up docker-down clean

help:
	@echo "Targets: install test run-api run-frontend lint build-frontend docker-build docker-up docker-down clean"

install: install-backend install-frontend

install-backend:
	$(PIP) install -r requirements.txt -r requirements-dev.txt

install-frontend:
	cd frontend && npm ci

test:
	$(PY) -m pytest -q

run-api:
	$(PY) -m uvicorn api.server:app --reload --host 0.0.0.0 --port 8000

run-frontend:
	cd frontend && npm run dev

lint:
	cd frontend && npm run lint

build-frontend:
	cd frontend && npm run build

docker-build:
	docker build -t hacktrek-api .

docker-up:
	docker compose up --build

docker-down:
	docker compose down

clean:
	rm -rf .pytest_cache api/__pycache__ tests/__pycache__
