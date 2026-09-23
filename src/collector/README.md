# Hyena Collector Blueprint

This directory provides collector-side runtime for hyena-v2 with direct
collector and bootboy entrypoints.

## Entrypoints

- collector.py
  - Implements data collection and output file generation.
- bootboy.py
  - Builds local config and manages system services/cron setup.

## Runtime Environment Variables

- ADSBEX_KEY
  - Optional ADS-B Exchange API key.

## Local Run

```bash
cd src/collector
source venv/bin/activate
python3 collector.py
```

## Bootboy Run

```bash
cd src/collector
source venv/bin/activate
python3 bootboy.py
```

## Notes

- Collected JSON is written to freshDir from the configuration file.
- config.example and bootboy defaults use /var/wombat/fresh/hyena.
