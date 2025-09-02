# Contributing

Thanks for contributing to fullon_ohlcv_api! This guide summarizes how to work effectively in this repo. For day‑to‑day conventions, see AGENTS.md.

We are a Poetry house. Always use `poetry install`, `poetry run ...`, or `poetry shell`. Do not use bare `pip` or `python` outside Poetry.

## Quick Start
- Prereqs: Python 3.11+, Poetry installed.
- Setup: `make setup` then configure `.env` from `env.example`.
- Run locally: `make dev` (Uvicorn reload) or `make prod`.

## Workflow
- Open an issue first with strategy + TDD plan (see `git_issues_rules.md`).
- Branch naming: `feature/<slug>` or `fix/<slug>` (e.g., `feature/timeseries-aggregation`).
- TDD: write failing tests, implement, iterate. Keep changes focused and small.
- Before pushing: `./run_test.py` and `make check` must pass. Coverage must remain 100%.
- Open a Pull Request using the provided template; link the issue (`Closes #123`).

## Code & Tests
- Style: Black (88), Ruff (includes import sort), mypy strict-ish (see `pyproject.toml`).
- Naming: files/modules `snake_case.py`; classes `PascalCase`; funcs/vars `snake_case`.
- Structure: routers in `src/fullon_ohlcv_api/routers/`, models in `models/`, shared deps in `dependencies/`.
- Tests: unit in `tests/unit/`, integration in `tests/integration/`. Prefer async tests where applicable.

## Logging & Security
- Logging: use `fullon_log.get_component_logger("fullon.api.ohlcv.<area>")` and structured fields (e.g., `logger.info("start", exchange=..., symbol=..., timeframe=...)`).
- Configuration: use `.env`; never commit secrets. Keep this API read‑only.

## References
- Contributor guide: see `AGENTS.md`.
- Issue authoring rules: `git_issues_rules.md`.
- Make targets: `make help` for a list.

Happy shipping! 🚀
