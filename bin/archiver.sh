#!/bin/bash
#
# Title: archiver.sh
# Description: tar success directory and save in export
# Development Environment: ubuntu 22.4.5 LTS
# Author: Guy Cole (guycole at gmail dot com)
#
PATH=/bin:/usr/bin:/etc:/usr/local/bin; export PATH
#
HOST_NAME=$(hostname)
TODAY=$(date '+%Y-%m-%d')
FILE_NAME="${HOST_NAME}-${TODAY}.tgz"
#
EXPORT_DIR="export"
SOURCE_DIR="hyena-v2"
SUCCESS_DIR_ADSB="success_adsb"
SUCCESS_DIR_UAT="success_uat"
WORK_DIR="/var/wombat/hyena"
#
echo "start archiver" 
#
cd ${WORK_DIR}
#
mv ${SUCCESS_DIR_ADSB} ${SOURCE_DIR}
mkdir ${SUCCESS_DIR_ADSB}
mv ${SUCCESS_DIR_UAT}/*.json ${SOURCE_DIR}
#
tar -cvzf ${FILE_NAME} ${SOURCE_DIR}
mv ${FILE_NAME} ${EXPORT_DIR}
#
echo "cleanup"
rm -rf ${SOURCE_DIR}
#
echo "end archiver"
#
