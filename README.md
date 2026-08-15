# SentinelLite

**A local-first Mini-SIEM for security learning, detection engineering, home labs, and small defensive teams.**

SentinelLite collects untrusted logs, selects a best-fit parser, normalizes investigation fields, preserves original evidence, evaluates YAML detections and correlations, and exposes the results through a documented API and responsive analyst dashboard.

Setup guides: [Українська](docs/quickstart-uk.md) · [Русский](docs/quickstart-ru.md) · [Deutsch](docs/quickstart-de.md) · [Polski](docs/quickstart-pl.md)

> Project status: **0.1.0 development release.** Useful end-to-end and tested, but not yet intended to replace a staffed enterprise SIEM.

## Features

- Built-in **Add logs** workbench for paste, batch, and bounded text-file ingestion
- Persistent submission journal with parser/status verification and links to raw evidence
- JSON, JSONL/NDJSON, CSV, TSV, key-value, syslog, SSH/auth, HTTP access, Windows/Sysmon-style, and firewall parsing
- Specialized parsers plus best-effort generic extraction and raw-event fallback for unknown log formats
- UTC timestamp normalization; validated IPv4/IPv6 and ports; field aliases; parser metadata
- PostgreSQL storage with Alembic migrations and investigation-focused indexes
- 14 version-controlled YAML rules: single-event, threshold, distinct-value, and ordered sequence detection
- Higher-confidence authentication-to-PowerShell correlation
- Event/alert timelines, raw evidence, MITRE context, notes, and analyst statuses
- Overview analytics, event explorer, alerts, detection rules, and observed hosts
- Fully local operation: no cloud API, telemetry export, or external log processing

## Screenshots

Screenshots will be added after the first tagged release. Run the Docker quick start below to view the complete responsive dark dashboard locally.

## Architecture

```text
Log sources → ingestion → parser selection → extraction → normalization
            → PostgreSQL → YAML detection → correlation → alerts
            → FastAPI → React dashboard
```

SentinelLite is a modular monolith rather than a distributed stack. See [architecture](docs/architecture.md), [log parsing](docs/log-parsing.md), and [detection engine](docs/detection-engine.md).

## Supported inputs

Upload `.txt`, `.log`, `.json`, `.jsonl`, `.ndjson`, `.csv`, or `.tsv`, or post strings/objects through the API. Specialized parsing covers common Linux SSH authentication, syslog, Apache/nginx-style access, firewall key-value, and flat Windows/Sysmon-style exports. Unknown text is heuristically inspected and always retains `raw_event`; SentinelLite does **not** claim to understand every log format perfectly.

## Docker quick start

Requirements: Docker Engine/Desktop with Compose v2.

```bash
git clone https://github.com/GGtascher/sentinellite.git
cd sentinellite
cp .env.example .env
# Edit .env and replace POSTGRES_PASSWORD.
docker compose up --build
```

Open:

- Dashboard: <http://localhost:3000>
- Add logs workbench: <http://localhost:3000/ingest>
- API: <http://localhost:8000/api/v1>
- OpenAPI docs: <http://localhost:8000/docs>
- Database-backed health: <http://localhost:8000/api/v1/health>

Stop with `docker compose down`. Add `-v` only when you intentionally want to delete local PostgreSQL data.

## Add and verify logs in the browser

Open <http://localhost:3000/ingest>. Paste one log, one event per line, a pretty JSON object, or a JSON array, then select **Submit and analyze**. You can also upload a UTF-8 `.txt`, `.log`, `.json`, `.jsonl`, `.ndjson`, `.csv`, or `.tsv` file. Built-in examples cover Linux SSH, Windows/Sysmon-style JSON, firewall key-value, Apache/nginx access, generic JSON, and unknown raw text.

The response separates parsed, partial, raw-fallback, and rejected records. The persistent **Submission journal** shows the latest 25 events sent from the workbench and links each item to its normalized fields, parser confidence, metadata, and preserved raw log. Unknown formats are safely retained; log content is never executed.

## Demo mode

With the stack running:

```bash
python scripts/generate_demo_events.py
```

The safe local generator submits fictional Windows logons, suspicious PowerShell, firewall denials/port variation, SSH, web failures, normal events, and an unknown-format event. It triggers several detections and correlation without executing any log content or contacting external infrastructure.

Sample files under `sample-data/` can be uploaded through the API:

```bash
curl -F "file=@sample-data/linux-auth.log" http://localhost:8000/api/v1/ingest/upload
curl -F "file=@sample-data/windows-events.json" http://localhost:8000/api/v1/ingest/upload
```

## API examples

```bash
curl -X POST http://localhost:8000/api/v1/ingest/event \
  -H "Content-Type: application/json" \
  -d '{"event":"Aug 15 14:31:11 lab sshd[12]: Failed password for root from 10.0.0.5 port 55422 ssh2"}'

curl "http://localhost:8000/api/v1/events?page=1&page_size=25&source_ip=10.0.0.5"
curl "http://localhost:8000/api/v1/alerts?severity=high&status=new"
```

Ingestion responses distinguish fully parsed, partially parsed, raw-fallback, and request-rejected records. An unknown format that can be stored safely is not reported as a parsing error.

## Project structure

```text
backend/app/       FastAPI, domain models, parsers, normalization, detection
backend/alembic/   Database migrations
backend/tests/     Unit/integration tests and deterministic parser corpus
frontend/src/      React/TypeScript analyst dashboard
rules/             YAML detection content by security category
sample-data/       Safe synthetic input examples
scripts/           Demo activity generator
docs/              Architecture, parsing, and detection documentation
```

## Development

Backend (Python 3.12+):

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
alembic upgrade head
uvicorn app.main:app --app-dir backend --reload
```

The default non-Docker database is local SQLite for contributor convenience; Docker and supported deployment use PostgreSQL. Override with `DATABASE_URL` to test PostgreSQL locally.

Frontend (Node 22+):

```bash
cd frontend
npm install
npm run dev
```

## Tests and quality checks

```bash
.venv/bin/python -m ruff check backend
.venv/bin/python -m pytest
cd frontend
npm test
npm run typecheck
npm run build
```

CI runs these checks plus Alembic offline SQL generation and Docker Compose configuration validation.

## Security and privacy

Logs are hostile data. SentinelLite uses validation, bounded uploads/events, extension allowlists, ORM queries, text-only rendering, and no command execution. Do not expose this V0.1 stack directly to untrusted networks: it has no authentication/RBAC yet. Change local database credentials, restrict listening interfaces/firewalls, and establish retention/backup policy for potentially sensitive logs. No logs leave the deployment unless an operator explicitly moves them. See [SECURITY.md](SECURITY.md).

## Roadmap

- Authenticated collectors and RBAC
- Retention controls, background ingestion, and live updates
- Linux/Windows agents and Sysmon streaming
- Sigma compatibility and more parsers
- Threat-intelligence enrichment with explicit local/privacy controls
- Email/webhook notifications
- Advanced correlation and multi-user investigations
- PCAP/network telemetry and OpenTelemetry ingestion

## Contributing

Contributions are welcome. Read [CONTRIBUTING.md](CONTRIBUTING.md) and the permanent engineering rules in [AGENTS.md](AGENTS.md). This project accepts defensive security functionality only.

## License

MIT. See [LICENSE](LICENSE). The neutral “SentinelLite contributors” holder should be reviewed by the repository owner before the first public tag.
