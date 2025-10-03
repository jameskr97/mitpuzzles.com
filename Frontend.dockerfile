############################################################
##### Build Arguments
ARG FRONTEND_IMAGE=docker.io/library/node:20-bookworm-slim
ARG VITE_POSTHOG_API_KEY

############################################################
##### Frontend Builder
FROM ${FRONTEND_IMAGE} AS frontend-builder
WORKDIR /app
COPY frontend/ /app
ENV VITE_POSTHOG_API_KEY=${VITE_POSTHOG_API_KEY}
RUN npm install && npm run build-prod

############################################################
##### Caddy with Static Files
FROM caddy:2-alpine

# Install jq for JSON manipulation
RUN apk add --no-cache jq

COPY --from=frontend-builder /app/dist/ /srv
COPY .docker/Caddyfile /etc/caddy/Caddyfile

# Add maintenance mode aliases
RUN echo 'alias m-on="echo \"{}\" > /srv/maintenance/maintenance.json && echo \"Maintenance mode enabled\""' >> /etc/profile && \
    echo 'alias m-off="rm -f /srv/maintenance/maintenance.json && echo \"Maintenance mode disabled\""' >> /etc/profile && \
    echo 'alias m-on-reason="echo \"{\\\"reason\\\": \\\"\$1\\\"}\" > /srv/maintenance/maintenance.json && echo \"Maintenance mode enabled with reason: \$1\""' >> /etc/profile && \
    echo 'alias m-status="if [ -f /srv/maintenance/maintenance.json ]; then echo \"Maintenance mode: ON\"; cat /srv/maintenance/maintenance.json | jq -r \".reason // \\\"No reason provided\\\"\"; else echo \"Maintenance mode: OFF\"; fi"' >> /etc/profile

EXPOSE 80 443
CMD ["caddy", "run", "--config", "/etc/caddy/Caddyfile", "--adapter", "caddyfile"]
