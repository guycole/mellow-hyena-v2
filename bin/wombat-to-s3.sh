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

for file in *; do
	[ -f "$file" ] || continue
	if aws s3 cp "$file" "${DEST_BUCKET}${file}" --profile="$HOST_NAME"; then
		mv -- "$file" "../${ARCHIVE_DIR}/"
	else
		echo "s3 copy failed for $file" >&2
		exit 1
	fi
done

echo "end s3 copy"
