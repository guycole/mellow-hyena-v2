#!/bin/bash
#
# Title: collector.sh
# Description: hyena collection
# Development Environment: Debian 10 (buster)/raspian
# Author: Guy Cole (guycole at gmail dot com)
#
PATH=/bin:/usr/bin:/etc:/usr/local/bin; export PATH
#LD_LIBRARY_PATH=/usr/local/lib/arm-linux-gnueabihf; export LD_LIBRARY_PATH
#
hostname=$(hostname)
logger -p local3.info "collector hyena $hostname"
#
WORK_DIR="$HOME/github/mellow-hyena-v2/src/collector"
# 
echo "start collection"
sleep 13
cd $WORK_DIR
source venv/bin/activate
python3 ./collector.py
echo "end collection"
#
