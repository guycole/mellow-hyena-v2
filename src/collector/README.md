# Hyena Collector Blueprint

This directory provides collector-side runtime for hyena-v2 and follows the same app pattern used by slug:

1. Small application entrypoint
2. Task worker classes
3. Environment-driven runtime behavior

## Entrypoints

- collector_app.py
  - Uses stuntbox mode routing.
  - Supported modes:
    - collector
    - bootboy
- collector.py
  - Implements data collection and output file generation.
- bootboy.py
  - Builds local config and manages system services/cron setup.

## Runtime Environment Variables

- stuntbox
  - Default: collector
- COLLECTOR_CONFIG
  - Default: config.yaml
- ADSBEX_KEY
  - Optional ADS-B Exchange API key.
- BOOTBOY_TARGET
  - Optional host override for bootboy mode.

## Local Run

```bash
cd src/collector
source venv/bin/activate
python3 collector_app.py
```

## Bootboy Run

```bash
cd src/collector
source venv/bin/activate
stuntbox=bootboy python3 collector_app.py
```

## Notes

- Collected JSON is written to freshDir from the configuration file.
- config.example and bootboy defaults use /var/wombat/fresh/hyena.
