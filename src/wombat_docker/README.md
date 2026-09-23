# Mellow Validator Blueprint (Hyena Wombat Docker)

This directory is a working example of a hyena validator and koala application.
It is designed to run either:

1. Locally with Python
2. In Docker with mounted data directories

## Purpose

The validator reads collected JSON files from a fresh directory, validates payloads,
records accepted files in PostgreSQL load-log storage, updates daily score, then
moves files to ADS-B/UAT success directories or failure.

The koala worker reads recent success files and emits condensed koala payload files.

## Components

### 1) Application Entrypoint

File: hyena_app.py

- Builds database connectivity from environment variables.
- Configures SQLAlchemy engine options (connection timeout, statement timeout, pool pre-ping).
- Routes execution by stuntbox mode.
- Modes:
   - validator
   - koala

### 2) Validator Engine

File: validator.py

- Iterates files in the configured fresh directory.
- Uses JsonHelper to validate file structure and content.
- Enforces idempotency by checking the load-log table for previously processed file names.
- Inserts load-log and updates daily-score metrics for valid files.
- On success: moves file to ADS-B or UAT success directory.
- On failure: moves file to failure directory.

### 3) Koala Generator

File: koala.py

- Scans success directories for JSON payloads.
- Selects the latest host payload per mode and writes a koala artifact.

### 4) Persistence Layer

Files: ../helper/postgres.py and ../helper/sql_table.py

- Implements data access methods used by the validator.
- Load-log and daily-score writes are performed during validation.

## Runtime Configuration

The runtime behavior is controlled by environment variables.

1. DB_CONN
2. PG_CONNECT_TIMEOUT (default 5)
3. PG_STATEMENT_TIMEOUT_MS (default 5000)
4. FRESH_DIR (default /var/wombat/fresh/hyena)
5. FAILURE_DIR (default /var/wombat/failure)
6. SUCCESS_DIR_ADSB (default /var/wombat/hyena/success_adsb)
7. SUCCESS_DIR_UAT (default /var/wombat/hyena/success_uat)
8. KOALA_DIR_ADSB (default /var/wombat/hyena/koala_adsb)
9. KOALA_DIR_UAT (default /var/wombat/hyena/koala_uat)
10. stuntbox (default validator)

## Local Run Pattern

```bash
cd src/wombat_docker
source venv/bin/activate
pip install -r requirements.txt

export DB_CONN="postgresql+psycopg2://hyena_client:batabat@localhost:5432/hyena"
export stuntbox="validator"
python hyena_app.py
```

Koala mode:

```bash
export stuntbox="koala"
python hyena_app.py
```

## Docker Run Pattern

Build:

```bash
docker build -f src/wombat_docker/Dockerfile -t hyena:latest src/
```

Run:

```bash
docker run \
   -e stuntbox=validator \
   -e DB_CONN="postgresql+psycopg2://hyena_client:batabat@172.17.0.1:5432/hyena" \
   -v /var/wombat:/mnt/wombat \
   --name hyena \
   hyena:latest
```
