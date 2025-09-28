# Copyright 2025 Google LLC

# Using your preferred uv-based setup
FROM python:3.12-slim

# Install uv, our package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set the working directory inside the container
WORKDIR /app

# Copy ONLY the contents of the remote_agent directory into /app
# This is the key change to isolate the agent's code and dependencies.
COPY remote_agent/ .

# Install the agent's specific dependencies from its own requirements.txt
RUN uv pip install -r requirements.txt

# Expose the port the container will listen on
EXPOSE 8080

# Set this environment variable to ensure logs are sent straight to the container logs
ENV PYTHONUNBUFFERED=1

# Run the app using its proper entry point from __main__.py
# We pass --port 8080 to match the EXPOSE instruction
ENTRYPOINT ["uv", "run", ".", "--host", "0.0.0.0", "--port", "8080"]
