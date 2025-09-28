# Copyright 2025 Google LLC
# FINAL - This Dockerfile will resolve the module not found error.

# Using your preferred uv-based setup
FROM python:3.12-slim

# Install uv, our package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set the working directory
WORKDIR /app

# Copy the application code from the build context (the remote_agent folder)
COPY . .

# Install dependencies from requirements.txt into the system's Python environment.
# This is the correct approach for a container.
RUN uv pip install --system -r requirements.txt

# Expose the port the container will listen on
EXPOSE 8080

# Ensure logs are sent straight to the container logs
ENV PYTHONUNBUFFERED=1

# Run the A2A server directly using Python.
# This is the most reliable way to run the app and ensures it finds the installed packages.
ENTRYPOINT ["python", "-m", "a2a.server", "--agent-class", "agent.ProductSellerAgent", "--port", "8080"]
