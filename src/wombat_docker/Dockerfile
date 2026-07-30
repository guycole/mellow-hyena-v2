#
# docker build -t hyena:latest -f src/wombat_docker/Dockerfile src/
# docker run -v /var/wombat:/mnt/wombat --name hyena hyena:latest
# docker run -e stuntbox=validate -v /var/wombat:/mnt/wombat --name hyena hyena:latest
# docker run -e stuntbox=score -e limit=5 --name hyena hyena:latest
# docker run -e stuntbox=score --name hyena hyena:latest
#
FROM python:3.11-slim

WORKDIR /app

ARG WOMBAT_UID=1000
ARG WOMBAT_GID=1000
ENV WOMBAT_UID=${WOMBAT_UID}
ENV WOMBAT_GID=${WOMBAT_GID}

# Ensure wombat exists, then persist its UID/GID discovered at build time.
RUN set -eux; \
	if ! getent group wombat >/dev/null 2>&1; then \
		addgroup --gid "$WOMBAT_GID" wombat; \
	fi; \
	if ! id -u wombat >/dev/null 2>&1; then \
		adduser --uid "$WOMBAT_UID" --gid "$WOMBAT_GID" --disabled-password --gecos "" wombat; \
	fi

RUN printf '%s\n' '#!/bin/sh' 'set -eu' \
	'uid="$(id -u wombat)"' \
	'gid="$(id -g wombat)"' \
	'printf "WOMBAT_UID=%s\nWOMBAT_GID=%s\n" "$uid" "$gid" > /app/wombat_env.env' \
	> /usr/local/bin/collect-wombat-ids.sh \
	&& chmod +x /usr/local/bin/collect-wombat-ids.sh

RUN /usr/local/bin/collect-wombat-ids.sh

# Create and activate virtualenv first
RUN python -m venv /app/venv
ENV VIRTUAL_ENV=/app/venv
ENV PATH="$VIRTUAL_ENV/bin:$PATH"

# Copy requirements and install them inside the venv
COPY wombat_docker/requirements.txt ./
RUN $VIRTUAL_ENV/bin/pip install --no-cache-dir -r requirements.txt

COPY wombat_docker/koala.py ./
COPY wombat_docker/hyena_app.py ./
COPY helper/ ./helper/
RUN touch /app/helper/__init__.py
COPY wombat_docker/validator.py ./

RUN printf '%s\n' '#!/bin/sh' 'set -e' '/usr/local/bin/collect-wombat-ids.sh' 'set -a' '[ -f /app/wombat_env.env ] && . /app/wombat_env.env' 'set +a' 'exec "$@"' > /usr/local/bin/docker-entrypoint.sh \
	&& chmod +x /usr/local/bin/docker-entrypoint.sh

ENV FAILURE_DIR=/mnt/wombat/failure/
ENV FRESH_DIR=/mnt/wombat/fresh/hyena
ENV KOALA_DIR_ADSB=/mnt/wombat/hyena/koala_adsb
ENV KOALA_DIR_UAT=/mnt/wombat/hyena/koala_uat
ENV SUCCESS_DIR_ADSB=/mnt/wombat/hyena/success_adsb/
ENV SUCCESS_DIR_UAT=/mnt/wombat/hyena/success_uat/

ENV DB_CONN=postgresql+psycopg2://hyena_client:batabat@172.17.0.1:5432/hyena

RUN mkdir -p /mnt/wombat
ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["python", "hyena_app.py"]
