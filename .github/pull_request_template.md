# Pull Request

## Summary
Describe the purpose of this PR in 1-3 sentences.

## Changes
- [ ] Briefly list key changes.

## Checklist
- [ ] Tests pass locally: `python3 -m pytest ai_product_manager/tests -v`
- [ ] Lint passes locally: `flake8 ai_product_manager --max-line-length=120 --exclude ui/.venv`
- [ ] Database migrations handled:
  - [ ] Generated migration (if models changed): `python3 -m ai_product_manager.tools.migrate revision -m "..." --autogenerate`
  - [ ] Reviewed migration for SQLite compatibility (no ALTER COLUMN TYPE). Adjusted if necessary.
  - [ ] Applied locally: `python3 -m ai_product_manager.tools.migrate upgrade head`
  - [ ] Migration drift check: `python3 -m ai_product_manager.tools.check_migrations`
- [ ] Artifacts/CLI run (optional but recommended):
  - [ ] `python3 -m ai_product_manager`
  - [ ] `python3 -m ai_product_manager.agent`
  - [ ] `streamlit run ai_product_manager/ui/app.py`

## Screenshots / Artifacts (if applicable)
Attach or link to relevant artifacts (e.g., `artifacts/status_*.md`, UI screenshots).

## Related Issues / Context
Link issues, discussions, or previous PRs.

## Notes for Reviewers
Anything reviewers should pay extra attention to (e.g., schema changes, API keys, rate limits).
