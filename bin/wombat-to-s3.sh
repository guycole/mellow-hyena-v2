#!/bin/bash
#
# Title: wombat-to-s3.sh
# Description: copy hyena files to s3 then move to archive
# Development Environment: Ubuntu 22.04.05 LTS
# Author: Guy Cole (guycole at gmail dot com)
#
PATH=/bin:/usr/bin:/etc:/usr/local/bin; export PATH
#
# host name is also AWS profile name
HOST_NAME=$(hostname)
#
ARCHIVE_DIR="archive"
EXPORT_DIR="export"
WORK_DIR="/var/wombat/hyena"
#
DEST_BUCKET=s3://mellow-hyena-uw2-t8833.braingang.net/fresh/
#
echo "start s3 copy"
cd "${WORK_DIR}/${EXPORT_DIR}" || exit 1

if aws s3 cp . "$DEST_BUCKET" --profile="$HOST_NAME"; then
	mv -- * "../${ARCHIVE_DIR}/"
else
	echo "s3 copy failed" >&2
	exit 1
fi

echo "end s3 copy"
