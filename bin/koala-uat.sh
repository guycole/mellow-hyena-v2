#!/bin/bash
#
# Title: koala-uat.sh
# Description: import koala files 
# Development Environment: Ubuntu 22.04.05 LTS
# Author: Guy Cole (guycole at gmail dot com)
#
RBENV_ROOT="${RBENV_ROOT:-/home/wombat/.rbenv}"
if [ ! -d "$RBENV_ROOT" ] && [ -d "$HOME/.rbenv" ]; then
  RBENV_ROOT="$HOME/.rbenv"
fi
PATH="$RBENV_ROOT/shims:$RBENV_ROOT/bin:/bin:/usr/bin:/etc:/usr/local/bin:/snap/bin${PATH:+:$PATH}"; export PATH
export RBENV_ROOT
#
#
SOURCE_DIR="/var/wombat/hyena/koala_uat"
KOALA_IMPORT="/home/wombat/github/mellow-koala/bin/import_hyena_uat"
#
for FILE in "$SOURCE_DIR"/*; do
  [ -f "$FILE" ] || continue

  "$KOALA_IMPORT" "$FILE"
  if [ $? -eq 0 ]; then
    rm "$FILE"
  else
    echo "ERROR: import failed for $FILE" >&2
  fi
done
#
