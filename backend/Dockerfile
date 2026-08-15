FROM python:3.12-slim
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
RUN addgroup --system sentinel && adduser --system --ingroup sentinel sentinel
COPY pyproject.toml alembic.ini ./
COPY backend ./backend
COPY rules ./rules
RUN pip install --no-cache-dir .
USER sentinel
EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --app-dir backend --host 0.0.0.0 --port 8000"]
