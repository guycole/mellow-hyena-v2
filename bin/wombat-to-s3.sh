#!/bin/bash
#
# Title: hyena-to-s3.sh
# Description: copy hyena files local file system to s3
# Development Environment: Ubuntu 22.04.05 LTS
# Author: Guy Cole (guycole at gmail dot com)
#
PATH=/bin:/usr/bin:/etc:/usr/local/bin; export PATH
#
AWS_PROFILE="$1"

if [[ -z "$AWS_PROFILE" ]]; then
	echo "usage: $0 <aws-profile>" >&2
	exit 1
fi

ARCHIVE_DIR="archive"
EXPORT_DIR="export"
WORK_DIR="/var/wombat/hyena"
#
DEST_BUCKET=s3://mellow-hyena-uw2-t8833.braingang.net/fresh/
#
echo "start s3 copy"
cd "${WORK_DIR}/${EXPORT_DIR}" || exit 1
mkdir -p "../${ARCHIVE_DIR}"

if aws s3 cp . "$DEST_BUCKET" --recursive --profile="$AWS_PROFILE"; then
	mv -- * "../${ARCHIVE_DIR}/"
else
	echo "s3 copy failed" >&2
	exit 1
fi

echo "end s3 copy"
