# SentinelLite engineering guide

## Purpose

SentinelLite is a defensive, local-first Mini-SIEM for learning, home labs, and small security teams. It ingests untrusted security logs, preserves originals, normalizes useful fields, applies documented YAML detections, and presents investigations through an API and dashboard. Never add offensive exploitation, credential theft, persistence deployment, or unrequested outbound telemetry.

## Architecture

The supported flow is `source -> ingestion -> parser selection -> extraction -> normalization -> PostgreSQL -> detection -> correlation -> alerts -> FastAPI -> React`. Backend modules must stay independently testable. Parsers return extracted data and confidence; normalization owns canonical fields; detections are data-driven YAML; service code coordinates transactions.

## Conventions

- Target Python 3.12+, use type hints, small functions, structured logging, and explicit errors.
- Keep HTTP handlers thin. Put domain work in services and database access behind SQLAlchemy sessions.
- Use Pydantic schemas at trust boundaries. Never concatenate SQL or execute log content.
- React code uses TypeScript strict mode, semantic HTML, accessible labels, reusable components, and escaped text rendering.
- Prefer pagination/batching. Do not load unbounded event sets.
- Preserve `raw_event`; never invent missing event timestamps.

## Backend

Add parsers through the `BaseParser` confidence interface and register them without changing orchestration behavior. Canonical aliases belong in normalization. Migrations are required for schema changes. Configuration comes from environment variables; no secrets in source.

## Frontend

Keep server state in the API layer and page state local unless shared state is justified. Every data view needs loading, error, and empty states. Severity/status presentation must remain consistent and the layout must work at mobile widths.

## Detection rules

Rules live under `rules/`, validate against the documented schema, have stable unique IDs, constrained severities, deterministic match conditions, and tests. MITRE ATT&CK mappings must be defensible. Threshold rules specify `group_by`, count, and timeframe. Never describe a rule as comprehensive detection coverage.

## Testing and security

Every behavior change requires relevant pytest and/or Vitest coverage. Include malformed and adversarial input for parsing boundaries. Treat filenames, uploads, JSON, YAML, filters, and log values as hostile. Enforce upload/event size limits, use safe paths and ORM queries, never render logs as HTML, and never send data to external services.

## Documentation and definition of done

Update README/API/architecture/parsing/detection documentation with behavioral changes. A task is done only when relevant backend tests, frontend tests, typecheck, and build pass; migrations are validated for database work; and Docker configuration is checked when deployment changes. Report any environment-blocked checks and exact commands for the maintainer. Do not claim unverified behavior.

