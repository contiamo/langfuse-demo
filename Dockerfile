FROM python:3.12-slim

WORKDIR /app

RUN pip install uv

COPY pyproject.toml .
RUN uv sync --no-dev --no-install-project

COPY src/ src/
RUN uv sync --no-dev

ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 7932
CMD ["uvicorn", "rag.agent:app", "--host", "0.0.0.0", "--port", "7932"]
