FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

# Установка curl для healthcheck
RUN apt-get update && apt-get install -y curl && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Копируем файлы проекта
COPY pyproject.toml uv.lock .python-version ./

# Устанавливаем зависимости через uv (без установки самого проекта)
RUN uv sync --frozen --no-dev --no-install-project

# Копируем исходный код после установки зависимостей
COPY src/ ./src/

# Создаем директорию для данных
RUN mkdir -p /app/data

# Expose порт
EXPOSE 8000

# Default command (переопределяется в docker-compose)
CMD ["uv", "run", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]


