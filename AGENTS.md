# AGENTS.md

## Purpose
- This file guides agentic coding tools for OpenInvoice.
- Follow repo tooling and style noted below.
- If instructions conflict, follow user prompts first.

## Repo Layout
- `server/`: Django + DRF backend.
- `dashboard/`: Vite + React + TanStack UI.
- Root `README.md` is minimal; per-project docs live in subdirs.

## Cursor/Copilot Rules
- No `.cursor/rules/*`, `.cursorrules`, or `.github/copilot-instructions.md` found.
- If added later, merge them into this guide.

## Global Conventions
- Keep changes minimal and consistent with existing patterns.
- Prefer existing abstractions over new utilities.
- Avoid unrelated refactors while implementing tasks.
- Use absolute imports only where configured (`@/*` in dashboard).
- Use `uv` for Python tooling and `pnpm` for dashboard tooling.

## Local Services (Docker Compose)
- Compose file: `docker-compose.yml`.
- Services: `postgresql` (5432), `mailpit` (8025/1025), `server` (8000), `dashboard` (5173).
- API container runs `migrate`, `collectstatic`, then `runserver` on start.
- Local DB credentials default to `postgres/postgres` with DB `postgres`.

## Backend (server/) Commands
- Install: `cd server && make install` (runs `uv install`).
- Lint: `cd server && make lint` (ruff check).
- Format: `cd server && make format` (ruff format + fix).
- Typecheck: `cd server && make typecheck` (mypy).
- Test: `cd server && make test` (pytest).
- All: `cd server && make all` (lint + format + typecheck + test).
- OpenAPI: `cd server && make openapi`.
- Migrations: `cd server && make migrations`.

## Backend Single-Test Examples
- File: `cd server && uv run pytest tests/path/test_file.py`.
- Test: `cd server && uv run pytest tests/path/test_file.py::test_name`.
- Keyword: `cd server && uv run pytest -k "keyword"`.
- With settings: uses `DJANGO_SETTINGS_MODULE=config.settings.test` via pytest config.

## OpenAPI + Orval Workflow
- Generate OpenAPI: `cd server && make openapi` (writes `dashboard/openapi.yaml`).
- Generate TS types/clients: `cd dashboard && pnpm orval` (uses `orval.config.ts`).
- Orval outputs: `dashboard/src/api/endpoints` (React Query hooks) and `dashboard/src/api/models` (schemas).
- Orval mutator: `dashboard/src/lib/api/client.ts` (`axiosInstance`).
- Flow: run OpenAPI generation first, then Orval to refresh queries/mutations.
- Keep generated files committed only if repo patterns show they are checked in.

## Frontend (dashboard/) Commands
- Install: `cd dashboard && pnpm install`.
- Dev server: `cd dashboard && pnpm dev` or `pnpm start`.
- Build: `cd dashboard && pnpm build` (vite build + tsc).
- Preview: `cd dashboard && pnpm serve`.
- Test: `cd dashboard && pnpm test` (Playwright).
- Lint: `cd dashboard && pnpm lint` (eslint).
- Format: `cd dashboard && pnpm format` (prettier).
- Typecheck: `cd dashboard && pnpm typecheck`.
- Generate API: `cd dashboard && pnpm orval`.

## Frontend Single-Test Examples
- Playwright file: `cd dashboard && pnpm test -- tests/path.spec.ts`.
- Playwright title: `cd dashboard && pnpm test -- -g "test name"`.
- Focus locally with `test.only` in Playwright when needed.

## Python Code Style (server/)
- Format with Ruff; line length is 120 (`pyproject.toml`).
- Use Ruff lint rules for naming, imports, and error handling.
- Avoid bare `except` blocks (ruff BLE).
- Use `pathlib.Path` instead of `os.path` (ruff PTH).
- No `print` statements (ruff T20); use logging where appropriate.
- Follow Django conventions: models/serializers/views by responsibility.
- Keep settings in `config/settings/*` and reference via env.
- Prefer explicit typing where non-obvious; mypy checks `apps`, `config`, `common`.
- Use `ClassVar` when annotating class attributes when needed.

## Django/DRF Patterns
- Prefer DRF serializers for validation and shaping responses.
- Use DRF exceptions (`ValidationError`, `NotFound`, etc.) for API errors.
- Leverage `drf-standardized-errors` output format in API responses.
- Keep query logic in `apps/*/querysets.py` where established.
- Keep reusable logic in `apps/*/models.py` amd `apps/*/managers.py`.
- Keep views thin; move complex logic into helpers.

## Python Naming
- `snake_case` for functions/variables/modules.
- `PascalCase` for classes and exceptions.
- `UPPER_SNAKE_CASE` for constants.
- Test names should read as behavior (`test_creates_invoice`).

## Python Imports
- Ruff `I` (isort) controls ordering; keep imports grouped.
- Standard library -> third-party -> local modules.
- Avoid unused imports (ruff F401).
- Avoid importing from `tests` in production code.

## Backend Testing
- Pytest config adds `-v --reuse-db`.
- Tests live under `server/tests`.
- Use factories (factory-boy) where available.
- Prefer deterministic tests; `pytest-randomly` is enabled.
- Always assert full `response.data` with explicit expected structures/values; do not use serializers to build assertions.

## TypeScript/React Code Style (dashboard/)
- TypeScript is strict (`tsconfig.json`).
- No unused locals/params; avoid `any`.
- Use `@/*` alias for `src` and `@tests/*` for tests.
- Keep components in PascalCase; hooks start with `use`.
- Favor function components and hooks over classes.
- Keep route files in `src/routes` (TanStack Router).

## Frontend Formatting
- Prettier with `prettier-plugin-tailwindcss` and import sorting.
- Run `pnpm format` before committing large changes.
- Keep Tailwind class order as formatter enforces.
- Prefer `clsx`/`cn` helpers (if present) for conditional classes.

## Frontend Linting
- ESLint uses `@tanstack/eslint-config`.
- Fix lint errors rather than disabling rules.
- Keep module syntax as ES modules (`"type": "module"`).

## TypeScript Naming
- `camelCase` for variables and functions.
- `PascalCase` for components, types, and enums.
- `UPPER_SNAKE_CASE` for constants.
- File names usually match exported component/hook.

## Error Handling (Frontend)
- Prefer explicit error states in UI (loading/error/success).
- Catch async errors in loaders/queries and show feedback.
- Avoid silent failures; surface errors via UI or logging.

## General Testing & CI Tips
- Run the smallest relevant test when iterating.
- Avoid running full suites unless needed.
- Keep snapshots stable and meaningful (if added).

## Documentation & Comments
- Update READMEs only when behavior changes.
- Avoid inline comments; prefer clear naming.
- Add docstrings to public functions if behavior is non-obvious.

## Safety & Secrets
- Never commit `.env` files or credentials.
- Use `django-environ` patterns for settings.

## Suggested Workflow
- Implement change.
- Format (`make format` or `pnpm format`).
- Lint/typecheck.
- Run focused tests.

## When in Doubt
- Search for similar patterns in existing files.
- Ask for clarification when behavior is unclear.
- Prefer small, reversible changes.

## Contact Points
- Backend: `server/README.md`.
- Frontend: `dashboard/README.md`.
