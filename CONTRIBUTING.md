# Contributing to SentinelLite

Thank you for helping build an understandable, defensive security tool.

## Workflow

1. Fork or clone the repository and create a focused branch: `git switch -c feat/short-description`.
2. Install backend and frontend dependencies using the README development steps.
3. Make small, typed, documented changes. Never commit `.env`, logs containing real sensitive data, tokens, or credentials.
4. Run relevant tests plus the full backend and frontend checks before opening a pull request.
5. Open a PR describing behavior, security impact, test evidence, migration/config changes, and screenshots for UI work.

## Add a parser

Implement the `LogParser` protocol under `backend/app/parsers/`, return a deterministic confidence score and `ParseResult`, and register it at the right layer in `ParserEngine`. Keep extraction side-effect free. Add positive, negative, malformed, IPv4/IPv6, and raw-preservation cases. Update `docs/log-parsing.md`.

## Add a detection rule

Add YAML under the relevant `rules/` category. Use a stable unique ID, supported severity, normalized field names, time-bounded thresholds/sequences, and only defensible MITRE mappings. Add tests proving both detection and non-detection, then update detection documentation when the schema changes.

## Quality gates

```bash
python -m ruff check backend
python -m pytest
cd frontend && npm test && npm run typecheck && npm run build
```

Schema changes require an Alembic migration and upgrade/downgrade validation. Deployment changes require `docker compose config` and, where Docker is available, a clean image build and health check. Follow `AGENTS.md` and keep all functionality defensive.
