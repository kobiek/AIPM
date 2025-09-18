# Makefile for AI Product Manager

PY=python3
PIP=$(PY) -m pip
PKG=ai_product_manager

.PHONY: help install dev-install migrate migrate-rev check-migrations test lint demo agent ui

help:
	@echo "Common targets:"
	@echo "  make install           - install requirements and package (editable)"
	@echo "  make migrate           - apply alembic upgrade head"
	@echo "  make migrate-rev msg=\"message\" - create autogen revision"
	@echo "  make check-migrations  - fail if autogen would create a revision"
	@echo "  make test              - run pytest"
	@echo "  make lint              - run flake8"
	@echo "  make demo              - run main CLI"
	@echo "  make agent             - run weekly agent"
	@echo "  make ui                - run Streamlit UI"

install:
	$(PIP) install --upgrade pip
	$(PIP) install -r $(PKG)/requirements.txt
	$(PIP) install -e $(PKG)

migrate:
	$(PY) -m $(PKG).tools.migrate upgrade head

migrate-rev:
	@if [ -z "$(msg)" ]; then echo "Usage: make migrate-rev msg=\"describe change\""; exit 1; fi
	$(PY) -m $(PKG).tools.migrate revision -m "$(msg)" --autogenerate

check-migrations:
	$(PY) -m $(PKG).tools.check_migrations

test:
	$(PY) -m pytest $(PKG)/tests -v

lint:
	$(PIP) install flake8
	flake8 $(PKG) --max-line-length=120 --exclude ui/.venv

demo:
	$(PY) -m $(PKG)

agent:
	$(PY) -m $(PKG).agent

ui:
	streamlit run $(PKG)/ui/app.py
