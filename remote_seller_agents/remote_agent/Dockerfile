# Copyright 2025 Google LLC

# Using your preferred uv-based setup
FROM python:3.12-slim

# Install uv, our package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Copy the application code into the container
ADD . /app
WORKDIR /app

# Install dependencies using the lock file for a reproducible environment
# This is the key change for reliable builds
RUN uv sync --frozen

# Expose the port the container will listen on
EXPOSE 8080

# Set this environment variable to ensure logs are sent straight to the container logs
ENV PYTHONUNBUFFERED=1

# Run the app using its proper entry point from __main__.py
# We pass --port 8080 to match the EXPOSE instruction
CMD ["python", "-m", "__main__", "--port", "8080"]
