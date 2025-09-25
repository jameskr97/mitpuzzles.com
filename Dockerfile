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
WORKDIR /app
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
COPY --from=frontend-builder /app/dist/ /app/static/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev

# set environment for production
ENV ENVIRONMENT=production
EXPOSE 8000

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]


#COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
#WORKDIR /app
#COPY README.md backend/ /app/
#RUN uv venv --relocatable --no-cache --directory /app/ /venv
#RUN . /venv/bin/activate && uv sync --directory /app/
#RUN ls /venv/bin

#############################################################
###### Final Image Builder
#FROM ${BACKEND_IMAGE} AS final
#WORKDIR /app
#EXPOSE 8000

### copy over app assets
#COPY --from=backend-builder /venv /venv
#COPY backend/ /app
#COPY --from=frontend-builder /app/dist/ /app/static
#RUN ls /venv/bin
### set environment variables

#ENV HOME='/app/'
#ENV PATH="/venv/bin:$PATH"
#ENV VIRTUAL_ENV="/venv"
#ENV DEBUG="False"
#### collectstatic + run
#RUN python manage.py collectstatic --noinput
#CMD ["/bin/ls", "/venv/bin"]
