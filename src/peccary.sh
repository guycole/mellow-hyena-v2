#!/bin/bash
#
# Title: peccary.sh
# Description: run the peccary hyena application
# Development Environment: Ubuntu 22.04.05 LTS
# Author: Guy Cole (guycole at gmail dot com)
#
PATH=/bin:/usr/bin:/etc:/usr/local/bin; export PATH
PYTHONPATH=$(pwd); export PYTHONPATH
DB_CONN="postgresql+psycopg2://hyena_client:batabat@localhost:5432/hyena"; export DB_CONN
#
source peccary_docker/venv/bin/activate
python peccary_docker/hyena_app.py
#