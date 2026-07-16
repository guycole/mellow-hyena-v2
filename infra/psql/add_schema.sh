#!/bin/bash
#
# Title:add_schema.sh
# Description:
# Development Environment: OS X 10.15.2/postgres 12.12
# Author: G.S. Cole (guy at shastrax dot com)
#
export PGDATABASE=hyena
export PGHOST=localhost
export PGPASSWORD=woofwoof
export PGUSER=hyena_admin
#
psql < adsb_exchange.psql
psql < daily_score.psql
psql < geo_loc.psql
psql < load_log.psql
psql < observation.psql
#
