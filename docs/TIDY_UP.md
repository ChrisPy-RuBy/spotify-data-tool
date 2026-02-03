# Repository Tidy-Up Checklist

## 1. Reorganise technical documentation

Move planning/development documents out of the repo root into `docs/`:

```
docs/
  NOTES.md
  TECHNICAL_RECOMMENDATIONS.md
  IMPLEMENTATION_PLAN_APPROACH3.md
  LABBOOK.md
```

These have historical value but don't belong at the root where they clutter the project for anyone browsing it.

## 2. Rewrite README.md

The current README is just the original brief. Replace it with a proper project README covering:

- What the tool does (FastAPI web app for exploring Spotify data exports)
- How to install dependencies (`uv sync`)
- How to run the dev server (`python main.py`)
- Project structure overview (`src/`, `src/api/`, `src/templates/`, `static/`, `tests/`)
- How to run tests (`uv run pytest`)

## 3. Rewrite CLAUDE.md

Every statement in the current CLAUDE.md is out of date:

- Says "early stage development" - it's a complete 5-phase app
- Says "basic hello world functionality" - it's a full FastAPI app
- Says "dependencies are currently empty" - there are 4 runtime + 3 dev deps
- Says "no test framework or linting tools configured" - has pytest, pre-commit, ruff

Rewrite to accurately describe the project, its structure, key commands, and conventions.

## 4. Remove manual test files from root

Delete the four manual test scripts from the project root:

- `test_loader_manual.py`
- `test_analytics_manual.py`
- `test_api_manual.py`
- `test_frontend_manual.py`

Proper automated tests already exist in `tests/`. If any of these are still useful as reference, move them to `docs/` or `scripts/` instead.

## 5. Update .gitignore

Add missing entries:

```
.pytest_cache/
data/
```

## 6. Delete stale git branches

**Merged branches (safe to delete from remote):**

- `feat-phase3-analytics`
- `feat-phase4-fastapi-backend`
- `feat-phase5-frontend-templates`
- `feat-project-eda`

**Abandoned phase-6 attempts (local and remote):**

- `feat-phase6-interactive-elements`
- `feat-phase6-interactive-features`
- `feat-phase6-performance-optimizations`
- `feat-phase6-search-filtering`

## 7. Resolve current branch

Currently on `feat-phase6-performance-optimizations-v2` with commit message "back this up whatever it is". Either merge to main if the work is worth keeping, or abandon it and start fresh from main.
