# Repository Guidelines

## Project Structure & Module Organization
- Source: `src/fullon_ohlcv_api/`
  - `routers/` (FastAPI endpoints), `models/` (Pydantic I/O), `dependencies/` (DB/session), `gateway.py`, `main.py`.
- Tests: `tests/unit/`, `tests/integration/`, shared fixtures in `tests/conftest.py`.
- Docs & examples: `docs/`, `examples/`.

## Build, Test, and Development Commands
- `make setup`: Install deps and copy `.env` from example.
- `make dev` / `make prod`: Run FastAPI via Uvicorn (reload vs prod).
- `make test` / `make test-cov`: Run full suite; the latter adds coverage.
- `make lint` / `make format`: Ruff+mypy; Black+Ruff fix.
- `make check`: Formatting check, lint, type-check, tests.
- Poetry equivalents:
  - `poetry install`
  - `poetry run python run_test.py`
  - `poetry run uvicorn src.fullon_ohlcv_api.main:app --reload`
  - `poetry run ruff check . && poetry run mypy src/`

## Coding Style & Naming Conventions
- Python 3.11+, 4-space indent, Black line length 88.
- Use type hints; imports sorted (Ruff `I`).
- Naming: files/modules `snake_case.py`; classes `PascalCase`; functions/vars `snake_case`; constants `UPPER_SNAKE`.
- Keep routers small and cohesive per resource.
- Logging: `from fullon_log import get_component_logger as gcl; logger = gcl("fullon.api.ohlcv.<area>")`; prefer structured logs, e.g. `logger.info("fetched", exchange=ex, symbol=sym, timeframe=tf)`.

## Testing Guidelines
- Frameworks: `pytest`, `pytest-asyncio`, `pytest-cov`.
- Coverage: 100% required; do not regress.
- Naming: unit `tests/unit/test_<area>.py`; integration under `tests/integration/`.
- Run locally: `poetry run python run_test.py`; for coverage use `make test-cov`.

## Commit & Pull Request Guidelines
- Commits: short, imperative subject; include scope when useful (e.g., `routers:`). Example: `routers: add trades range endpoint validation`.
- Reference issues in body (`Closes #123`). Keep changes focused and atomic.
- PRs: explain motivation, behavior change, and verification (`make check` clean). Merge only with green CI and updated tests/docs.

## Issue & Branch Workflow
- Open an issue with strategy and TDD plan.
- Branch naming: `feature/<slug>` (e.g., `feature/timeseries-aggregation`).
- Follow TDD: write failing tests, implement, iterate; keep routers/models cohesive.

## Security & Configuration Tips
- Configure via `.env` (copy `env.example` → `.env`); never commit secrets.
- This API is read-only; avoid introducing writes.
- Prefer dependency injection via `dependencies/`; never use global state.

## Architecture Overview
- FastAPI routers compose a read-only gateway (LRRS principles).
- Separate concerns: routing, validation (Pydantic), data access.
- New endpoints live in `src/fullon_ohlcv_api/routers/` with matching models in `models/`.

## Related Docs
- Project structure: [@docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md)
- LLM quickstart: [@docs/FULLON_OHLCV_LLM_QUICKSTART.md](docs/FULLON_OHLCV_LLM_QUICKSTART.md)
- Method reference: [@docs/FULLON_OHLCV_METHOD_REFERENCE.md](docs/FULLON_OHLCV_METHOD_REFERENCE.md)
- Logging guide: [@docs/FULLON_LOG_LLM_REAMDE.md](docs/FULLON_LOG_LLM_REAMDE.md)
- Model guidance: [CLAUDE.md](CLAUDE.md)
