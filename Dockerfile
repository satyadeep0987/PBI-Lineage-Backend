FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY pyproject.toml uv.lock ./

RUN uv sync \
    --locked \
    --no-dev \
    --no-install-project

COPY app ./app

RUN uv sync \
    --locked \
    --no-dev

EXPOSE 8000

CMD ["uv", "run", "--no-sync", "fastapi", "run", "--port", "8000"]