FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --home /app --shell /usr/sbin/nologin app

# Install dependencies first for better layer caching. A temporary package stub lets
# setuptools resolve pyproject.toml before the full application tree is copied.
COPY pyproject.toml ./
RUN mkdir -p app \
    && touch app/__init__.py \
    && pip install --no-cache-dir . \
    && rm -rf app beyondresume_backend.egg-info

COPY alembic.ini ./
COPY alembic ./alembic
COPY app ./app
COPY docker-entrypoint.sh ./

# Reinstall so site-packages includes the real application package and package data.
RUN pip install --no-cache-dir --no-deps . \
    && chmod +x /app/docker-entrypoint.sh \
    && mkdir -p /app/data/uploads \
    && chown -R app:app /app

USER app

EXPOSE 8000

# Invoke via /bin/sh so startup does not depend solely on the executable bit
# (Windows checkouts may lose +x; .gitattributes keeps LF endings).
CMD ["/bin/sh", "/app/docker-entrypoint.sh"]
