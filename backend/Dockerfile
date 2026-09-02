FROM python:3.13-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN addgroup --system appgroup \
    && adduser --system --ingroup appgroup appuser

COPY requirements.txt requirements-dev.txt ./

RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

FROM base AS test

RUN pip install --no-cache-dir -r requirements-dev.txt

COPY app ./app
COPY alembic.ini ./
COPY migrations ./migrations
COPY tests ./tests

RUN chown -R appuser:appgroup /app

USER appuser

CMD ["pytest", "-q"]

FROM base AS production

COPY app ./app
COPY alembic.ini ./
COPY migrations ./migrations

RUN mkdir -p /var/lib/cloud-security/archive \
    && chown -R appuser:appgroup /app /var/lib/cloud-security/archive

USER appuser

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
