# Copyright 2025 Google LLC

# Using your preferred uv-based setup
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

RUN apt-get update && apt-get install -y \
    curl \
    && rm -rf /var/lib/apt/lists/*

ADD . /app
WORKDIR /app

# Note: uv sync will use pyproject.toml if it exists, otherwise it can use requirements.txt
RUN uv pip install -r requirements.txt

EXPOSE 8080

ENV PYTHONUNBUFFERED=1

# Run the FastAPI app using uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
