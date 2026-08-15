# SentinelLite: завантаження, запуск і перевірка

Ця інструкція дозволяє запустити весь SentinelLite локально через Docker: PostgreSQL, FastAPI та вебінтерфейс React. Жодні журнали не відправляються у зовнішні сервіси.

## 1. Що потрібно встановити

- [Git](https://git-scm.com/downloads)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/) для Windows або macOS; у Linux — Docker Engine із Compose v2
- приблизно 2 ГБ вільного місця для образів та локальної бази

Переконайтеся, що Docker Desktop запущений. Перевірка:

```powershell
docker --version
docker compose version
```

Обидві команди мають показати версію, а не помилку.

## 2. Завантаження проєкту

Відкрийте PowerShell або Terminal і виконайте:

```powershell
git clone https://github.com/GGtascher/sentinellite.git
cd sentinellite
```

Якщо проєкт уже завантажений:

```powershell
cd sentinellite
git pull
```

## 3. Налаштування середовища

Windows PowerShell:

```powershell
Copy-Item .env.example .env
notepad .env
```

Звичайний Windows Command Prompt (`cmd.exe`):

```bat
copy .env.example .env
notepad .env
```

`Copy-Item` працює лише у PowerShell. Якщо запрошення виглядає як `C:\Users\name>`, ви, найімовірніше, використовуєте `cmd.exe`, тому використовуйте команду `copy`.

Linux або macOS:

```bash
cp .env.example .env
```

У `.env` обов'язково замініть:

```dotenv
POSTGRES_PASSWORD=change-me-local-only
```

на власний локальний пароль, наприклад довгий випадковий рядок без пробілів. Не публікуйте `.env`: файл уже виключено з Git.

## 4. Запуск застосунку

У корені репозиторію виконайте:

```powershell
docker compose up --build
```

Перший запуск може тривати кілька хвилин. Дочекайтеся, поки сервіси `db`, `backend` і `frontend` стануть healthy. Не закривайте це вікно термінала під час роботи програми.

Запуск у фоні:

```powershell
docker compose up --build -d
docker compose ps
```

## 5. Що відкрити

- Вебінтерфейс: <http://localhost:3000>
- API: <http://localhost:8000/api/v1>
- Інтерактивна документація API: <http://localhost:8000/docs>
- Перевірка стану: <http://localhost:8000/api/v1/health>

Health endpoint має повернути приблизно:

```json
{"status":"healthy","database":"available","version":"0.1.0"}
```

## 6. Запуск демонстрації

Генератор використовує лише безпечні вигадані події. Він нічого не виконує з журналів і не звертається до зовнішньої інфраструктури.

Якщо на комп'ютері встановлено Python 3.12 або новіший:

```powershell
python scripts/generate_demo_events.py
```

Якщо команда `python` не знайдена, у Windows спробуйте:

```powershell
py scripts/generate_demo_events.py
```

Очікуваний результат для чистої бази:

- 29 подій прийнято;
- події видно на сторінці **Events**;
- на сторінці **Alerts** з'являються кілька спрацювань;
- серед них є Windows brute force, підозрілий PowerShell, мережеві та веб-пороги;
- кореляція `CORR-001` створює критичний alert для послідовності «невдалі входи → успішний вхід → підозрілий процес».

Оновіть <http://localhost:3000> після завершення генератора.

## 7. Перевірка завантаження власного тестового файла

У репозиторії є безпечні синтетичні приклади в `sample-data/`. PowerShell:

```powershell
curl.exe -F "file=@sample-data/linux-auth.log" http://localhost:8000/api/v1/ingest/upload
curl.exe -F "file=@sample-data/windows-events.json" http://localhost:8000/api/v1/ingest/upload
```

Відповідь показує кількість повністю розібраних, частково розібраних, raw-fallback і відхилених подій. Невідомий формат не вважається помилкою, якщо SentinelLite може безпечно зберегти оригінальний `raw_event`.

## 8. Повна перевірка функціональності

1. Відкрийте **Overview** — мають відображатися лічильники подій, alert-ів і хостів.
2. Відкрийте **Events** — таблиця повинна містити події демо.
3. Натисніть подію — перевірте normalized fields, parser confidence і **Raw event**.
4. Відкрийте **Alerts** — має бути список детекцій із severity та status.
5. Відкрийте `Authentication compromise sequence` — перевірте timeline і supporting events.
6. Змініть статус на `Investigating`, додайте нотатку і натисніть **Save investigation**.
7. Відкрийте **Detection rules** — повинні завантажитися 14 YAML-правил.
8. Відкрийте **Hosts** — мають бути `win-lab-01`, `linux-lab` та інші спостережені хости.

Перевірка через API:

```powershell
curl.exe http://localhost:8000/api/v1/statistics
curl.exe "http://localhost:8000/api/v1/events?page=1&page_size=5"
curl.exe "http://localhost:8000/api/v1/alerts?page=1&page_size=20"
curl.exe http://localhost:8000/api/v1/rules
```

## 9. Зупинка та очищення

Зупинити контейнери, але зберегти базу:

```powershell
docker compose down
```

Зупинити й видалити локальну базу SentinelLite:

```powershell
docker compose down -v
```

Команда з `-v` безповоротно видаляє події та alert-и з локального Docker volume. Використовуйте її лише коли дані більше не потрібні.

## 10. Типові проблеми

### Docker не знайдено

Запустіть Docker Desktop, дочекайтеся статусу «Engine running» і відкрийте нове вікно PowerShell.

### Порт 3000 або 8000 уже зайнятий

Зупиніть іншу програму на цьому порту або змініть ліву частину відповідного `ports` у `docker-compose.yml`.

### Backend або база не стають healthy

```powershell
docker compose ps
docker compose logs db
docker compose logs backend
```

Перевірте, що `POSTGRES_PASSWORD` заданий у `.env`. Якщо ви змінили пароль після першого запуску і тестові дані не потрібні, виконайте `docker compose down -v`, а потім запустіть стек знову.

### Повністю чистий повторний запуск

```powershell
docker compose down -v
docker compose build --no-cache
docker compose up
```

## Безпека

V0.1 призначена для локального або довіреного лабораторного середовища. У ній ще немає автентифікації та RBAC, тому не публікуйте порти 3000, 8000 або PostgreSQL безпосередньо в Інтернет. Не завантажуйте реальні журнали з паролями, токенами чи персональними даними без належного дозволу та політики зберігання.
