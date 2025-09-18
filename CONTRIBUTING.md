# Contributing to AI Product Manager

Thanks for contributing! This guide helps you set up your environment, make changes safely, and pass CI.

## Environment setup
- Python 3.9+
- Install package and dependencies (editable):
  ```bash
  python3 -m pip install -e ai_product_manager
  python3 -m pip install -r ai_product_manager/requirements.txt
  ```
- Optional environment variables:
  - `GEMINI_API_KEY` (LLM synthesis and PRD drafts)
  - `GITHUB_TOKEN` (GitHub rate limits)
  - `SERPAPI_API_KEY` (SerpAPI News connector)
  - `AIPM_DB_PATH` or `AIPM_DB_URL` (SQLite path / SQLAlchemy URL)

## Database migrations (Alembic)
- Generate a migration after changing models (in `ai_product_manager/persistence/models.py`):
  ```bash
  python3 -m ai_product_manager.tools.migrate revision -m "describe change" --autogenerate
  ```
- Review the created file under `ai_product_manager/alembic/versions/`.
  - For SQLite, avoid `ALTER COLUMN TYPE` (not supported). If autogen produced type-alter ops, replace with table copy or skip if harmless in dev.
- Apply migrations locally:
  ```bash
  python3 -m ai_product_manager.tools.migrate upgrade head
  ```

## Pre-push checks
- Run tests and lint:
  ```bash
  python3 -m pytest ai_product_manager/tests -v
  python3 -m pip install flake8
  flake8 ai_product_manager --max-line-length=120 --exclude ui/.venv
  ```
- Check migration drift:
  ```bash
  python3 -m ai_product_manager.tools.check_migrations
  ```
- Smoke run CLI and Agent:
  ```bash
  python3 -m ai_product_manager
  python3 -m ai_product_manager.agent
  ```
- Optional: Streamlit UI
  ```bash
  streamlit run ai_product_manager/ui/app.py
  ```

## Commit & PR tips
- Keep changes scoped and described clearly.
- Include migration files in the same PR as model changes.
- Reference related issues or artifacts when relevant (e.g., status reports, insights, evaluation).

Thanks again for helping improve the project!
