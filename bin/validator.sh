#!/bin/bash
#
# Title: validator.sh
# Description: verify collection files and update stats for wombat
# Development Environment: Ubuntu 22.04.05 LTS
# Author: Guy Cole (guycole at gmail dot com)
#
PATH=/bin:/usr/bin:/etc:/usr/local/bin; export PATH
#
CONTAINER1="wombat-hyena"
CONTAINER2="koala-hyena"
IMAGE="ghcr.io/guycole/wombat-hyena:latest"
#
WOMBAT_UID=$(id -u wombat)
WOMBAT_GID=$(id -g wombat)
#
echo "start validate"
#
docker rm ${CONTAINER1};docker run -e WOMBAT_UID=${WOMBAT_UID} -e WOMBAT_GID=${WOMBAT_GID} -v /var/wombat:/mnt/wombat --name ${CONTAINER1} ${IMAGE}
#
#
docker rm ${CONTAINER2};docker run -e stuntbox=koala -v /var/wombat:/mnt/wombat --name ${CONTAINER2} ${IMAGE}
#
echo "end validate"
#
