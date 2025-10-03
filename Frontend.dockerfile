############################################################
##### Build Arguments
ARG FRONTEND_IMAGE=docker.io/library/node:20-bookworm-slim

############################################################
##### Frontend Builder
FROM ${FRONTEND_IMAGE} AS frontend-builder
WORKDIR /app
COPY frontend/ /app
RUN npm install && npm run build-prod

############################################################
##### Caddy with Static Files
FROM caddy:2-alpine
COPY --from=frontend-builder /app/dist/ /srv
COPY .docker/Caddyfile /etc/caddy/Caddyfile
EXPOSE 80 443
CMD ["caddy", "run", "--config", "/etc/caddy/Caddyfile", "--adapter", "caddyfile"]
