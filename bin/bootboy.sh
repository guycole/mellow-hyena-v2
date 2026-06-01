#!/bin/bash
#
# Title: bootboy.sh
# Description: configure 
# Development Environment: Ubuntu 22.04.05 LTS
# Author: Guy Cole (guycole at gmail dot com)
#
PATH=/bin:/usr/bin:/etc:/usr/local/bin; export PATH
#
WORK_DIR="/home/wombat/Documents/github/mellow-heeler-v2/src/collector"
#
echo "start bootboy"

if ! command -v systemctl >/dev/null 2>&1; then
	echo "systemctl not found" >&2
	exit 1
fi

# Let systemd own dump1090 startup by enabling the unit, but do not start it here.
systemctl enable dump1090.service

cd $WORK_DIR
source venv/bin/activate
python3 ./bootboy.py
echo "end bootboy"
#
