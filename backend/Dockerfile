FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml ./
RUN pip install --no-cache-dir .

COPY . .
# Ensure the entrypoint is executable even when checked out on Windows without +x.
RUN chmod +x /app/docker-entrypoint.sh

EXPOSE 8000

# Invoke via /bin/sh so startup does not depend solely on the executable bit.
CMD ["/bin/sh", "/app/docker-entrypoint.sh"]
