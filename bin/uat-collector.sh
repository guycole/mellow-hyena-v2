#!/bin/bash
#
# Title: uat-collector.sh
# Description: dump978 collection
# Development Environment: Debian 10 (buster)/raspian
# Author: Guy Cole (guycole at gmail dot com)
#
# * * * * * /ho/gsc/Documents/github/mellow-hyena/bin/adsb-collector.sh > /dev/null 2>&1
#
PATH=/bin:/usr/bin:/etc:/usr/local/bin; export PATH
#LD_LIBRARY_PATH=/usr/local/lib/arm-linux-gnueabihf; export LD_LIBRARY_PATH
#
WORK_DIR="/home/wombat/Documents/github/mellow-hyena-v2/src/collector"
# 
echo "start collection"
sleep 13
cd $WORK_DIR
source venv/bin/activate
python3 ./collector.py uat
echo "end collection"
#
