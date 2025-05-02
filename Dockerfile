############################################################
##### Build Arguments
ARG FRONTEND_IMAGE=docker.io/library/node:20-bookworm-slim
ARG BACKEND_IMAGE=docker.io/library/python:3.13-slim

############################################################
##### Frontend Builder
FROM ${FRONTEND_IMAGE} AS frontend-builder
WORKDIR /app
COPY frontend/ /app
RUN npm install && npm run build-prod

############################################################
##### Backend Builder
FROM ${BACKEND_IMAGE} AS backend-builder
ENV PIP_DEFAULT_TIMEOUT=100 \
    # Allow statements and log messages to immediately appear
    PYTHONUNBUFFERED=1 \
    # disable a pip version check to reduce run-time & log-spam
    PIP_DISABLE_PIP_VERSION_CHECK=1

## Setup python build environment
### copy requirements.txt
COPY backend/requirements/ requirements/
### prepare virtual environment
RUN python -m venv --copies /venv
ENV PATH="/venv/bin:$PATH"
ENV VIRTUAL_ENV="/venv"
RUN python -m pip install --no-cache-dir --upgrade pip
### install packages
RUN pip install --no-cache-dir -r requirements/base.txt

############################################################
##### Final Image Builder
FROM ${BACKEND_IMAGE} AS final
WORKDIR /app
EXPOSE 8000

### copy over app assets
COPY --from=backend-builder /venv /venv
COPY backend/ .
COPY --from=frontend-builder /app/dist/static /app/frontend_dist

### set environment variables
ENV HOME='/app/'
ENV PATH="/venv/bin:$PATH"
ENV VIRTUAL_ENV="/venv"
ENV DJANGO_ENV="production"
ENV DEBUG="False"

### collectstatic + run
RUN python manage.py collectstatic --noinput
CMD ["/venv/bin/uvicorn", "config.asgi:application", "--host", "0.0.0.0"]
