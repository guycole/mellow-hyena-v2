#!/bin/bash
#
# Title: loader.sh
# Description: load hyena files
# Development Environment: Ubuntu 22.04.05 LTS
# Author: Guy Cole (guycole at gmail dot com)
#
PATH=/bin:/usr/bin:/etc:/usr/local/bin; export PATH
#
hostname=$(hostname)
logger -p local3.info "hyena loader $hostname"
#
echo "start load"
#
docker rm hyena;docker run -v /var/peccary/hyena:/mnt/peccary/hyena --name hyena hyena:latest
#
echo "end load"
#
