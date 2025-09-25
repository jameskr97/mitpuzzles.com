FROM mcr.microsoft.com/devcontainers/python:3.13
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
RUN curl -fsSL https://deb.nodesource.com/setup_20.x | bash - && apt-get install -y nodejs
WORKDIR /workspace
CMD ["sleep", "infinity"]
