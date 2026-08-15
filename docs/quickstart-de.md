# SentinelLite herunterladen, starten und testen

Diese Anleitung startet SentinelLite vollständig lokal mit Docker: PostgreSQL, FastAPI und die React-Weboberfläche. Protokolldaten werden nicht an externe Dienste gesendet.

## 1. Voraussetzungen

- [Git](https://git-scm.com/downloads)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) für Windows/macOS oder Docker Engine mit Compose v2 für Linux
- Python 3.12+ wird nur für den lokalen Demo-Generator benötigt

Docker Desktop muss laufen. Prüfen Sie:

```bat
docker --version
docker compose version
```

Beide Befehle müssen eine Version ausgeben. Falls `docker` nicht erkannt wird, installieren/starten Sie Docker Desktop und öffnen Sie danach ein neues Terminal.

## 2. Projekt herunterladen

Windows Command Prompt:

```bat
cd %USERPROFILE%
git clone https://github.com/GGtascher/sentinellite.git
cd sentinellite
```

Ein vorhandenes Repository aktualisieren:

```bat
cd %USERPROFILE%\sentinellite
git pull
```

## 3. Umgebung konfigurieren

Windows Command Prompt (`cmd.exe`):

```bat
copy .env.example .env
notepad .env
```

Windows PowerShell:

```powershell
Copy-Item .env.example .env
notepad .env
```

Linux/macOS:

```bash
cp .env.example .env
```

Ersetzen Sie in `.env` den Wert `POSTGRES_PASSWORD=change-me-local-only` durch ein eigenes langes lokales Passwort ohne Leerzeichen. Veröffentlichen Sie die `.env`-Datei nicht.

## 4. Anwendung starten

Im Verzeichnis `sentinellite`:

```bat
docker compose up --build
```

Der erste Build kann einige Minuten dauern. Start im Hintergrund:

```bat
docker compose up --build -d
docker compose ps
```

Die Dienste `db`, `backend` und `frontend` sollten den Zustand healthy erreichen.

## 5. Anwendung öffnen

- Dashboard: <http://localhost:3000>
- Integrierte Protokolleingabe und Prüfung: <http://localhost:3000/ingest>
- API: <http://localhost:8000/api/v1>
- OpenAPI-Dokumentation: <http://localhost:8000/docs>
- Systemzustand: <http://localhost:8000/api/v1/health>

Der Health Endpoint sollte `status: healthy` und `database: available` zurückgeben.

Auf **Add logs** können Sie ein Ereignis, ein Ereignis pro Zeile, ein formatiertes JSON-Objekt oder ein JSON-Array einfügen und **Submit and analyze** wählen. Alternativ laden Sie eine UTF-8-Datei mit der Endung `.txt`, `.log`, `.json`, `.jsonl`, `.ndjson`, `.csv` oder `.tsv` hoch. Beispiele erklären Linux SSH, Windows/Sysmon JSON, Firewall-`key=value`, Apache/nginx und generisches JSON. Das Journal der letzten 25 Einsendungen wird in PostgreSQL gespeichert und verlinkt normalisierte sowie rohe Ereignisdaten. Unbekannte Formate bleiben sicher als `raw_fallback` erhalten.

## 6. Demo-Daten erzeugen

Öffnen Sie ein zweites Terminal:

```bat
cd %USERPROFILE%\sentinellite
python scripts\generate_demo_events.py
```

Unter Windows funktioniert alternativ:

```bat
py scripts\generate_demo_events.py
```

Bei einer leeren Datenbank sendet das Skript 29 fiktive Ereignisse. Es erzeugt unter anderem Windows-Brute-Force-, verdächtige-PowerShell-, Netzwerk- und Web-Alarme sowie die kritische Korrelation `CORR-001`.

## 7. Funktionen prüfen

1. **Overview** zeigt Ereignis-, Alarm- und Host-Zähler.
2. **Events** enthält die Demo-Ereignisse.
3. Eine Ereignisdetailseite zeigt normalisierte Felder, Parser-Konfidenz und **Raw event**.
4. **Alerts** zeigt Severity und Bearbeitungsstatus.
5. `Authentication compromise sequence` enthält eine Timeline und unterstützende Ereignisse.
6. Setzen Sie den Status auf `Investigating`, ergänzen Sie eine Notiz und speichern Sie.
7. **Detection rules** zeigt 14 YAML-Regeln.
8. **Hosts** zeigt die beobachteten Systeme.

Eine sichere Beispieldatei hochladen:

```bat
curl.exe -F "file=@sample-data/linux-auth.log" http://localhost:8000/api/v1/ingest/upload
```

## 8. Beenden und Daten löschen

Container stoppen, Daten behalten:

```bat
docker compose down
```

Container und lokale Datenbank löschen:

```bat
docker compose down -v
```

Die Option `-v` löscht lokale Ereignisse und Alarme unwiderruflich.

## Fehlerdiagnose

```bat
docker compose ps
docker compose logs db
docker compose logs backend
docker compose logs frontend
```

Wenn das Datenbankpasswort nach dem ersten Start geändert wurde und die Testdaten nicht benötigt werden, führen Sie `docker compose down -v` und anschließend `docker compose up --build` aus.

## Sicherheit

V0.1 ist für eine lokale, vertrauenswürdige Laborumgebung vorgesehen. Authentifizierung und RBAC sind noch nicht implementiert. Veröffentlichen Sie die Ports nicht direkt im Internet und laden Sie keine echten Geheimnisse oder personenbezogenen Protokolle ohne Erlaubnis hoch.
