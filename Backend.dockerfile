############################################################
##### Build Arguments
ARG BACKEND_IMAGE=docker.io/library/python:3.13-slim

############################################################
##### Backend Builder
FROM ${BACKEND_IMAGE} AS backend-builder
WORKDIR /app

# install build dependencies for native extensions (pypblib needs g++)
RUN apt-get update && apt-get install -y --no-install-recommends \
    g++ \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# set uv environment variables
ENV UV_COMPILE_BYTECODE=1
ENV UV_LINK_MODE=copy
ENV PATH="/app/.venv/bin:$PATH"

# install dependencies first
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=backend/uv.lock,target=uv.lock \
    --mount=type=bind,source=backend/pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project --no-dev

# copy project files
COPY backend/ /app/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

# set environment for production
ENV ENVIRONMENT=production
EXPOSE 8000

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
