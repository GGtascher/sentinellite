# Contributing to SentinelLite

SentinelLite is a defensive security project focused on understandable log processing, detection engineering, and investigation workflows.

Changes should be focused, testable, and documented.

## Development Workflow

1. Fork or clone the repository.
2. Create a focused branch.

```bash
git switch -c feat/short-description
```

3. Install the backend and frontend dependencies using the development instructions in `README.md`.
4. Make the required change.
5. Add or update tests when behavior changes.
6. Run the relevant quality checks.
7. Open a pull request describing:
   - what changed;
   - why the change was needed;
   - security implications, if any;
   - tests performed;
   - configuration or migration changes;
   - screenshots for visible UI changes.

## General Guidelines

- Keep functions focused and understandable.
- Use Python type hints where appropriate.
- Keep HTTP handlers thin and place domain logic in the appropriate application modules.
- Use Pydantic models at API trust boundaries.
- Use SQLAlchemy rather than manually concatenating SQL.
- Treat uploaded logs, filenames, JSON, YAML, filters, and event values as untrusted data.
- Never execute content extracted from a log.
- Preserve `raw_event` when ingesting security records.
- Do not invent event timestamps when the source does not provide one.
- Do not add unnecessary external telemetry or cloud dependencies.
- Never commit credentials, tokens, real sensitive logs, or `.env` files.

## Adding a Parser

Parsers belong under:

```text
backend/app/parsers/
```

A parser should:

- provide deterministic format recognition;
- extract useful fields without side effects;
- preserve unknown data where appropriate;
- handle malformed input safely;
- avoid executing or interpreting log content as code.

Add tests for:

- expected input;
- non-matching input;
- malformed input;
- IPv4 and IPv6 where relevant;
- raw-event preservation.

Update:

```text
docs/log-parsing.md
```

when parser behavior or supported formats change.

## Adding a Detection Rule

Detection rules live under:

```text
rules/
```

Use:

- a stable and unique rule ID;
- supported severity values;
- normalized field names;
- clear grouping;
- documented thresholds or sequences;
- defensible MITRE ATT&CK mappings.

New rules should include positive and negative test cases.

Do not describe a rule as comprehensive detection coverage.

## Backend Quality Checks

Run:

```bash
python -m ruff check backend
python -m pytest
```

## Frontend Quality Checks

Run:

```bash
cd frontend
npm test
npm run typecheck
npm run build
```

## Database Changes

Schema changes require an Alembic migration.

Validate migration generation and application before submitting the change.

## Deployment Changes

Changes affecting Docker or deployment configuration should include:

```bash
docker compose config
```

and, when Docker is available, a clean build and health check.

## Documentation

Documentation should be updated whenever behavior, configuration, supported formats, or user-visible functionality changes.

Do not claim functionality that has not been tested or implemented.

## Security Scope

SentinelLite accepts defensive security functionality.

Do not contribute functionality intended for:

- credential theft;
- unauthorized exploitation;
- malware deployment;
- persistence installation;
- destructive activity;
- unrequested outbound collection of user data.
