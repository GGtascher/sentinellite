# SentinelLite

**A local-first Mini-SIEM for security learning, detection engineering, home labs, and small defensive teams.**

SentinelLite ingests security logs, selects an appropriate parser, normalizes investigation fields, preserves original evidence, evaluates YAML-based detections and correlations, and presents the results through a FastAPI backend and React analyst dashboard.

> Project status: **0.1.0 development release.** The project is functional end-to-end and covered by automated tests, but it is not intended to replace an enterprise SIEM.

## Screenshot

<img width="1269" height="701" alt="SentinelLite dashboard" src="https://github.com/user-attachments/assets/af58dff5-9681-4dda-9259-5cc49cb0e3de" />

## Features

- Single-event, batch, multiline, and bounded text-file ingestion
- JSON, JSONL/NDJSON, CSV, TSV, key-value, syslog, SSH/auth, HTTP access, Windows/Sysmon-style, and firewall parsing
- Specialized parsers with generic extraction and raw-event fallback for unknown formats
- UTC timestamp normalization
- IPv4/IPv6 and port validation
- PostgreSQL storage with Alembic migrations
- 14 version-controlled YAML detection rules
- Single-event, threshold, distinct-value, and ordered-sequence detections
- Authentication-to-PowerShell correlation
- Event and alert timelines
- Raw evidence preservation
- MITRE ATT&CK context
- Analyst notes and alert statuses
- Overview analytics, event explorer, alerts, rules, and observed-host views
- Fully local operation with no cloud telemetry or external log processing

## Architecture

```text
Log sources
    ↓
Ingestion
    ↓
Parser selection
    ↓
Extraction
    ↓
Normalization
    ↓
PostgreSQL
    ↓
YAML detection
    ↓
Correlation
    ↓
Alerts
    ↓
FastAPI
    ↓
React dashboard
```

SentinelLite uses a modular-monolith architecture rather than a distributed stack.

More detailed documentation:

- [Architecture](docs/architecture.md)
- [Log parsing](docs/log-parsing.md)
- [Detection engine](docs/detection-engine.md)

## Supported Inputs

SentinelLite accepts:

- `.txt`
- `.log`
- `.json`
- `.jsonl`
- `.ndjson`
- `.csv`
- `.tsv`

Events can also be submitted directly through the API.

Specialized parsing currently covers common:

- Linux SSH authentication logs
- syslog records
- Apache/nginx-style HTTP access logs
- firewall key-value records
- Windows/Sysmon-style exports

Unknown text can still be stored through the raw-event fallback. SentinelLite does not claim to perfectly understand every log format.

## Docker Quick Start

Requirements:

- Docker Engine or Docker Desktop
- Docker Compose v2

Clone the repository:

```bash
git clone https://github.com/dmytrooliinyk-cyber/sentinellite.git
cd sentinellite
```

Create the local environment file:

```bash
cp .env.example .env
```

Edit `.env` and replace the example PostgreSQL password.

Start the stack:

```bash
docker compose up --build
```

Open:

- Dashboard: <http://localhost:3000>
- API: <http://localhost:8000/api/v1>
- OpenAPI documentation: <http://localhost:8000/docs>
- Health endpoint: <http://localhost:8000/api/v1/health>

Stop the stack with:

```bash
docker compose down
```

Use `docker compose down -v` only when you intentionally want to remove the local PostgreSQL data volume.

## Troubleshooting

### PostgreSQL Authentication Failed

If the backend fails to start with the following error:

```text
FATAL: password authentication failed for user "sentinellite"
```

**Cause:** PostgreSQL stores its credentials in a persistent Docker volume. Changing `POSTGRES_PASSWORD` in `.env` does not automatically update the password of an existing database.

**Solution 1 — Preserve existing data (recommended)**

Start the database container:

```bash
docker compose up -d db
```

Connect to PostgreSQL:

```bash
docker compose exec db psql -U sentinellite -d sentinellite
```

Update the database password:

```sql
\password sentinellite
```

Enter the password currently configured in `.env`, then exit with `\q`.

Restart the application:

```bash
docker compose up -d --build
```

**Solution 2 — Reset the database (development only)**

If existing data is not needed:

```bash
docker compose down -v
docker compose up -d --build
```

**Warning:** This permanently deletes the PostgreSQL Docker volume, including stored events, alerts, and investigation data.

### Verify Container Health

Check that all services are running:

```bash
docker compose ps
```

Inspect backend logs if necessary:

```bash
docker compose logs backend --tail=100
```

**Note:** Always keep database credentials consistent with your `.env` configuration. Never commit `.env` files containing real passwords to GitHub.


## Demo Data

With the application running:

```bash
python scripts/generate_demo_events.py
```

The generator submits fictional security events including:

- Windows logons
- suspicious PowerShell activity
- firewall denials
- SSH authentication activity
- web failures
- normal events
- an unknown-format event

The script is designed to exercise the detection pipeline without executing log contents or contacting external infrastructure.

Sample files are also available under `sample-data/`.

Example:

```bash
curl -F "file=@sample-data/linux-auth.log" http://localhost:8000/api/v1/ingest/upload
curl -F "file=@sample-data/windows-events.json" http://localhost:8000/api/v1/ingest/upload
```

## API Examples

Submit an event:

```bash
curl -X POST http://localhost:8000/api/v1/ingest/event \
  -H "Content-Type: application/json" \
  -d '{"event":"Aug 15 14:31:11 lab sshd[12]: Failed password for root from 10.0.0.5 port 55422 ssh2"}'
```

Query events:

```bash
curl "http://localhost:8000/api/v1/events?page=1&page_size=25&source_ip=10.0.0.5"
```

Query alerts:

```bash
curl "http://localhost:8000/api/v1/alerts?severity=high&status=new"
```

Ingestion responses distinguish fully parsed, partially parsed, raw-fallback, and rejected records.

An unfamiliar format that can be safely stored is not automatically treated as a parsing failure.

## Project Structure

```text
sentinellite/
├── backend/
│   ├── app/
│   ├── alembic/
│   └── tests/
├── frontend/
│   └── src/
├── rules/
├── sample-data/
├── scripts/
├── docs/
├── docker-compose.yml
├── README.md
├── SECURITY.md
└── CONTRIBUTING.md
```

### Main areas

- `backend/app/` — FastAPI, models, parsers, normalization, detection, correlation
- `backend/alembic/` — database migrations
- `backend/tests/` — backend unit and integration tests
- `frontend/src/` — React and TypeScript analyst dashboard
- `rules/` — YAML detection rules
- `sample-data/` — safe synthetic log samples
- `scripts/` — demo-data utilities
- `docs/` — technical documentation

## Local Development

### Backend

Python 3.12+ is recommended.

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

On Windows:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install development dependencies:

```bash
pip install -e ".[dev]"
```

Apply migrations:

```bash
alembic upgrade head
```

Start the backend:

```bash
uvicorn app.main:app --app-dir backend --reload
```

The non-Docker development configuration can use local SQLite for convenience. Docker deployments use PostgreSQL.

Override `DATABASE_URL` when testing another database configuration.

### Frontend

```bash
cd frontend
npm install
npm run dev
```

## Tests and Quality Checks

Backend:

```bash
python -m ruff check backend
python -m pytest
```

Frontend:

```bash
cd frontend
npm test
npm run typecheck
npm run build
```

CI additionally validates Alembic offline SQL generation and the Docker Compose configuration.

## Security and Privacy

Security logs must be treated as untrusted input.

SentinelLite uses:

- bounded uploads and event sizes
- extension allowlists
- structured validation
- SQLAlchemy ORM queries
- text-only rendering of log values
- no execution of log contents
- local processing without external telemetry

Version 0.1 does not include authentication or RBAC, so the application should not be exposed directly to untrusted networks.

Potentially sensitive logs should be protected with appropriate firewall rules, credentials, retention policies, and backups.

See [SECURITY.md](SECURITY.md) for additional information.

## Limitations

SentinelLite is a learning and portfolio project rather than an enterprise SIEM.

Current limitations include:

- no authentication or multi-user RBAC
- no dedicated endpoint agents
- no enterprise-scale ingestion architecture
- no distributed processing
- no built-in threat-intelligence service
- best-effort parsing for unknown formats
- limited correlation compared with mature commercial SIEM platforms

Detection results should be treated as investigation signals rather than proof of compromise.

## Roadmap

- Authenticated collectors and RBAC
- Retention controls
- Background ingestion
- Live event updates
- Linux and Windows collectors
- Sysmon streaming
- Sigma compatibility
- Additional parsers
- Optional threat-intelligence enrichment
- Email and webhook notifications
- Advanced correlation
- Multi-user investigations
- PCAP and network telemetry support
- OpenTelemetry ingestion

## Contributing

Contributions are welcome.

See [CONTRIBUTING.md](CONTRIBUTING.md) for development conventions, testing requirements, and guidelines for adding parsers or detection rules.

The project is focused on defensive security functionality.

## License

Released under the [MIT License](LICENSE).
