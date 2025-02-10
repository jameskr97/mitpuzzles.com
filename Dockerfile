############################################################
##### Build Arguments
ARG FRONTEND_IMAGE=docker.io/library/node:20-bookworm-slim
ARG BACKEND_IMAGE=docker.io/library/python:3.13-slim

############################################################
##### Frontend Builder
FROM ${FRONTEND_IMAGE} AS frontend-builder
WORKDIR /app
COPY frontend/ /app
RUN npm install && npm run build

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
COPY backend/requirements.txt requirements.txt
### prepare virtual environment
RUN python -m venv --copies /venv
ENV PATH="/venv/bin:$PATH"
ENV VIRTUAL_ENV="/venv"
RUN python -m pip install --no-cache-dir --upgrade pip
### install packages
RUN pip install --no-cache-dir -r requirements.txt

############################################################
##### Final Image Builder
FROM ${BACKEND_IMAGE} AS final
WORKDIR /app
EXPOSE 8000

### copy over app assets
COPY --from=backend-builder /venv /venv
COPY backend/ .
COPY --from=frontend-builder /app/dist /app/frontend_dist

### set environment variables
ENV HOME='/app/'
ENV PATH="/venv/bin:$PATH"
ENV VIRTUAL_ENV="/venv"

### collectstatic with dummy environment variables
RUN python manage.py collectstatic --noinput

# This DJANGO_ENV must be set after collectstatic.
# collectstatic uses local environment variables in order to generate the correct static files.
# If DJANGO_ENV is set before collectstatic, the environment variable validation will prevent collectstatic from running.
ENV DJANGO_ENV="production"
ENV DEBUG="False"
CMD ["/venv/bin/uvicorn", "mitlogic.asgi:application", "--host", "0.0.0.0"]