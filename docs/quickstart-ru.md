# SentinelLite: скачивание, запуск и проверка

Эта инструкция запускает полный SentinelLite локально через Docker: PostgreSQL, FastAPI и веб-интерфейс React. Пользовательские журналы не отправляются во внешние сервисы.

## 1. Требования

- [Git](https://git-scm.com/downloads)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) для Windows/macOS или Docker Engine с Compose v2 для Linux
- Python 3.12+ требуется только для локального демо-генератора

Запустите Docker Desktop и проверьте:

```bat
docker --version
docker compose version
```

Обе команды должны вывести версии. Если `docker` не распознан, установите/запустите Docker Desktop и откройте новое окно терминала.

## 2. Скачать проект

```bat
cd %USERPROFILE%
git clone https://github.com/GGtascher/sentinellite.git
cd sentinellite
```

Для обновления уже скачанного проекта:

```bat
cd %USERPROFILE%\sentinellite
git pull
```

## 3. Создать `.env`

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

В `.env` обязательно замените `POSTGRES_PASSWORD=change-me-local-only` на собственный длинный локальный пароль без пробелов. Не публикуйте `.env`.

## 4. Запустить SentinelLite

Из каталога `sentinellite`:

```bat
docker compose up --build
```

Первый запуск может занять несколько минут. Для фонового режима:

```bat
docker compose up --build -d
docker compose ps
```

Сервисы `db`, `backend` и `frontend` должны перейти в состояние healthy.

## 5. Открыть приложение

- Панель: <http://localhost:3000>
- Встроенное добавление и проверка логов: <http://localhost:3000/ingest>
- API: <http://localhost:8000/api/v1>
- Swagger/OpenAPI: <http://localhost:8000/docs>
- Состояние системы: <http://localhost:8000/api/v1/health>

Health endpoint должен вернуть `status: healthy` и `database: available`.

На странице **Add logs** вставьте один лог, по одному логу в каждой строке, форматированный JSON-объект или JSON-массив и нажмите **Submit and analyze**. Здесь же можно загрузить UTF-8 файл `.txt`, `.log`, `.json`, `.jsonl`, `.ndjson`, `.csv` или `.tsv`. Готовые примеры показывают Linux SSH, Windows/Sysmon JSON, firewall `key=value`, Apache/nginx и generic JSON. Журнал последних 25 отправлений хранится в PostgreSQL и ведёт к нормализованному и исходному событию. Неизвестный формат безопасно сохраняется как `raw_fallback`.

## 6. Создать демонстрационные события

В новом терминале:

```bat
cd %USERPROFILE%\sentinellite
python scripts\generate_demo_events.py
```

В Windows также можно использовать:

```bat
py scripts\generate_demo_events.py
```

Для чистой базы генератор отправляет 29 вымышленных событий и создаёт несколько alert-ов: Windows brute force, подозрительный PowerShell, сетевые/веб-пороги и критическую корреляцию `CORR-001`.

## 7. Проверить интерфейс

1. **Overview** — счётчики событий, alert-ов и хостов.
2. **Events** — таблица демонстрационных событий.
3. Откройте событие — проверьте normalized fields, parser confidence и неизменённый **Raw event**.
4. **Alerts** — список детекций с severity и status.
5. Откройте `Authentication compromise sequence` — проверьте timeline и supporting events.
6. Измените status на `Investigating`, добавьте заметку и сохраните.
7. **Detection rules** — должны отображаться 14 YAML-правил.
8. **Hosts** — список замеченных хостов.

Загрузка безопасного примера:

```bat
curl.exe -F "file=@sample-data/linux-auth.log" http://localhost:8000/api/v1/ingest/upload
```

## 8. Остановить или очистить

Остановить с сохранением базы:

```bat
docker compose down
```

Удалить контейнеры и локальную базу:

```bat
docker compose down -v
```

`-v` безвозвратно удаляет локальные события и alert-ы.

## Проблемы

Проверьте состояние и логи:

```bat
docker compose ps
docker compose logs db
docker compose logs backend
docker compose logs frontend
```

Если пароль менялся после первого запуска и тестовые данные не нужны, выполните `docker compose down -v`, затем `docker compose up --build`.

## Безопасность

V0.1 предназначена для локальной доверенной лаборатории. Аутентификации и RBAC пока нет: не публикуйте порты приложения напрямую в Интернет и не загружайте реальные секреты или персональные журналы без разрешения.
