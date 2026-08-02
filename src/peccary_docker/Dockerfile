#
# Build from the src/ directory (one level above this file):
# docker build -f peccary_docker/Dockerfile -t peccary:latest .
# docker run -e WOMBAT_UID=<uid> -e WOMBAT_GID=<gid> -v /var/peccary:/mnt/peccary --name peccary peccary:latest
#
FROM python:3.11-slim

WORKDIR /app

# Create and activate virtualenv first
RUN python -m venv /app/venv
ENV VIRTUAL_ENV=/app/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Copy requirements and install them inside the venv
COPY peccary_docker/requirements.txt ./
RUN $VIRTUAL_ENV/bin/pip install --no-cache-dir -r requirements.txt

COPY helper/ ./helper/
COPY peccary_docker/hyena_app.py ./
COPY peccary_docker/loader.py ./

RUN printf '%s\n' '#!/bin/sh' 'set -eu' \
	': "${WOMBAT_UID:?WOMBAT_UID is required}"' \
	': "${WOMBAT_GID:?WOMBAT_GID is required}"' \
	'exec "$@"' > /usr/local/bin/docker-entrypoint.sh \
	&& chmod +x /usr/local/bin/docker-entrypoint.sh

ENV FAILURE_DIR=/mnt/peccary/hyena/failure
ENV FRESH_DIR=/mnt/peccary/hyena/hyena-v2

# On Linux (production): override with -e DB_CONN=...@172.17.0.1:5432/hyena
# On macOS (Docker Desktop): host.docker.internal resolves to the host machine
ENV DB_CONN=postgresql+psycopg2://hyena_client:batabat@host.docker.internal:5432/hyena

RUN mkdir -p /mnt/peccary
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["python", "hyena_app.py"]
