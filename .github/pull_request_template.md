## PR Title
Short, imperative, scoped. Example: `routers: add timeseries OHLCV endpoint`.

## Linked Issue
Closes #<issue-number>

## Summary
What and why (problem, approach, scope). Note any behavioral changes.

## Changes
- Key change 1
- Key change 2

## Checklist
- [ ] Tests added/updated for all changes
- [ ] `./run_test.py` passes locally
- [ ] `make check` passes (black --check, ruff, mypy, tests)
- [ ] Coverage remains at 100%
- [ ] Docs updated (README/docs/AGENTS.md) when behavior changes
- [ ] Logging uses `fullon_log.get_component_logger(...)` with structured fields
- [ ] No secrets committed; config via `.env`

## Verification
Commands used to verify the change locally:

```bash
make setup               # first time only
make check               # formatting, lint, types, tests
./run_test.py            # full suite
# optional: run server
make dev
# example cURL
curl -s http://localhost:8000/docs >/dev/null
```

## Breaking Changes
Describe any breaking changes and migration notes, or write “None”.

## Screenshots / API Examples (optional)
Add cURL snippets or response examples if relevant.

