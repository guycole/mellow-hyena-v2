#!/bin/bash
#
# Title: wombat.sh
# Description: run the wombat hyena application
# Development Environment: Ubuntu 22.04.05 LTS
# Author: Guy Cole (guycole at gmail dot com)
#
PATH=/bin:/usr/bin:/etc:/usr/local/bin; export PATH
PYTHONPATH=$(pwd); export PYTHONPATH
#
source wombat_docker/venv/bin/activate
python wombat_docker/hyena_app.py
#