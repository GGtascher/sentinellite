# SentinelLite: pobieranie, uruchamianie i testowanie

Ta instrukcja uruchamia cały SentinelLite lokalnie przez Docker: PostgreSQL, FastAPI oraz interfejs React. Logi użytkownika nie są wysyłane do usług zewnętrznych.

## 1. Wymagania

- [Git](https://git-scm.com/downloads)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) dla Windows/macOS albo Docker Engine z Compose v2 dla Linux
- Python 3.12+ jest potrzebny tylko do lokalnego generatora demonstracyjnego

Uruchom Docker Desktop i sprawdź:

```bat
docker --version
docker compose version
```

Obie komendy powinny wyświetlić wersję. Jeśli `docker` nie jest rozpoznawany, zainstaluj/uruchom Docker Desktop i otwórz nowe okno terminala.

## 2. Pobranie projektu

Windows Command Prompt:

```bat
cd %USERPROFILE%
git clone https://github.com/GGtascher/sentinellite.git
cd sentinellite
```

Aktualizacja istniejącej kopii:

```bat
cd %USERPROFILE%\sentinellite
git pull
```

## 3. Konfiguracja środowiska

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

W pliku `.env` zmień `POSTGRES_PASSWORD=change-me-local-only` na własne długie hasło lokalne bez spacji. Nie publikuj pliku `.env`.

## 4. Uruchomienie aplikacji

W katalogu `sentinellite`:

```bat
docker compose up --build
```

Pierwsza kompilacja może potrwać kilka minut. Uruchomienie w tle:

```bat
docker compose up --build -d
docker compose ps
```

Usługi `db`, `backend` i `frontend` powinny osiągnąć stan healthy.

## 5. Adresy aplikacji

- Panel: <http://localhost:3000>
- Wbudowane dodawanie i sprawdzanie logów: <http://localhost:3000/ingest>
- API: <http://localhost:8000/api/v1>
- Dokumentacja OpenAPI: <http://localhost:8000/docs>
- Stan systemu: <http://localhost:8000/api/v1/health>

Endpoint zdrowia powinien zwrócić `status: healthy` oraz `database: available`.

Na stronie **Add logs** wklej pojedynczy log, po jednym zdarzeniu w wierszu, sformatowany obiekt JSON albo tablicę JSON i wybierz **Submit and analyze**. Możesz też przesłać plik UTF-8 `.txt`, `.log`, `.json`, `.jsonl`, `.ndjson`, `.csv` lub `.tsv`. Gotowe przykłady obejmują Linux SSH, Windows/Sysmon JSON, firewall `key=value`, Apache/nginx i ogólny JSON. Dziennik ostatnich 25 wysłanych zdarzeń jest przechowywany w PostgreSQL i prowadzi do danych znormalizowanych oraz surowego logu. Nieznany format jest bezpiecznie zachowywany jako `raw_fallback`.

## 6. Dane demonstracyjne

Otwórz drugi terminal:

```bat
cd %USERPROFILE%\sentinellite
python scripts\generate_demo_events.py
```

W Windows możesz też użyć:

```bat
py scripts\generate_demo_events.py
```

Dla pustej bazy generator wysyła 29 fikcyjnych zdarzeń. Powstają alerty Windows brute force, podejrzanego PowerShell, progów sieciowych i webowych oraz krytyczna korelacja `CORR-001`.

## 7. Sprawdzenie funkcji

1. **Overview** pokazuje liczniki zdarzeń, alertów i hostów.
2. **Events** zawiera zdarzenia demonstracyjne.
3. Szczegóły zdarzenia pokazują pola znormalizowane, pewność parsera i **Raw event**.
4. **Alerts** pokazuje severity i status analityka.
5. `Authentication compromise sequence` zawiera oś czasu i zdarzenia wspierające.
6. Ustaw status `Investigating`, dodaj notatkę i zapisz.
7. **Detection rules** powinno pokazywać 14 reguł YAML.
8. **Hosts** pokazuje zaobserwowane systemy.

Wysłanie bezpiecznego przykładu:

```bat
curl.exe -F "file=@sample-data/linux-auth.log" http://localhost:8000/api/v1/ingest/upload
```

## 8. Zatrzymanie i czyszczenie

Zatrzymanie z zachowaniem danych:

```bat
docker compose down
```

Usunięcie kontenerów i lokalnej bazy:

```bat
docker compose down -v
```

Opcja `-v` nieodwracalnie usuwa lokalne zdarzenia i alerty.

## Rozwiązywanie problemów

```bat
docker compose ps
docker compose logs db
docker compose logs backend
docker compose logs frontend
```

Jeżeli hasło bazy zmieniono po pierwszym uruchomieniu, a dane testowe nie są potrzebne, wykonaj `docker compose down -v`, a następnie `docker compose up --build`.

## Bezpieczeństwo

V0.1 jest przeznaczony do lokalnego, zaufanego laboratorium. Uwierzytelnianie i RBAC nie są jeszcze dostępne. Nie wystawiaj portów bezpośrednio do Internetu i nie przesyłaj prawdziwych sekretów ani danych osobowych bez odpowiedniego zezwolenia.
