#!/bin/bash
#
# Title: hyena-validate.sh
# Description: verify collection files and write stats
# Development Environment: Ubuntu 22.04.05 LTS
# Author: Guy Cole (guycole at gmail dot com)
#
PATH=/bin:/usr/bin:/etc:/usr/local/bin; export PATH
#
echo "start validate"
#
docker rm hyena-validate;docker run -v /var/wombat:/mnt/wombat --name hyena-validate hyena:latest
#
docker rm hyena-koala;docker run -e stuntbox=koala -v /var/wombat:/mnt/wombat --name hyena-koala hyena:latest
#
/home/wombat/github/mellow-wombat/bin/hyena-adsb-koala-import.sh
/home/wombat/github/mellow-wombat/bin/hyena-uat-koala-import.sh
#
echo "end validate"
#
