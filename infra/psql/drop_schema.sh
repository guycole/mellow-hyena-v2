#!/bin/bash
#
# Title:drop_schema.sh
# Description: remove schema
# Development Environment: OS X 10.15.2/postgres 12.12
# Author: G.S. Cole (guy at shastrax dot com)
#
export PGDATABASE=hyena
export PGHOST=localhost
export PGPASSWORD=woofwoof
export PGUSER=hyena_admin
#
psql $PGDATABASE -c "drop table hyena_observation"
psql $PGDATABASE -c "drop table hyena_adsb_exchange"
psql $PGDATABASE -c "drop table hyena_daily_score"
psql $PGDATABASE -c "drop table hyena_load_log"
psql $PGDATABASE -c "drop table hyena_geo_loc"
#
