FROM python:3.12-slim

WORKDIR /app

RUN pip install uv

COPY pyproject.toml .
RUN uv sync --no-dev --no-install-project

COPY src/ src/
COPY frontend/ frontend/
COPY entrypoint.sh /entrypoint.sh
RUN uv sync --no-dev && chmod +x /entrypoint.sh

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 7932
CMD ["/entrypoint.sh"]
