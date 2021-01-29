#!/bin/bash
# The set -e tells bash to exit immediately if a simple command fails.
# The set -o pipefail tells bash to set pipeline's return status to status of the last (rightmost) command.
set -e
set -o pipefail

# This script loads postgres epa wqx dump filesinto the wqx_schema.
# Enviroment variables needed:
export DB_ADDRESS=localhost
export EPA_SCHEMA_OWNER_USERNAME=epa_owner
export EPA_DB_OWNER_PASSWORD=changeMe
export EPA_DATABASE_NAME=db_name
export EPA_WQX_DUMP_DIR=.  # directory where Postgresq pg_dump achive files are located

# Optional DATABASE_PORT defaults to 5432
if [ -z "$DATABASE_PORT" ]; then
  export DATABASE_PORT=5432
fi

export PATH=/mingw64/bin:$PATH

if [ -z "$DB_ADDRESS" ]; then
  echo "The Postgres host name (DB_ADDRESS) to connect to is not defined."
  exit 2
fi

if [ -z "$EPA_DATABASE_NAME" ]; then
  echo "The database name (EPA_DATABASE_NAME) to restore into is not defined."
  exit 2
fi

if [ -z "$EPA_SCHEMA_OWNER_USERNAME" ]; then
  echo "The database user (EPA_SCHEMA_OWNER_USERNAME) is not defined."
  exit 2
fi

if [ -z "$EPA_SCHEMA_OWNER_PASSWORD" ]; then
  echo "The database password (EPA_SCHEMA_OWNER_PASSWORD) is not defined."
  exit 2
fi

if [ -z "$EPA_WQX_DUMP_DIR" ]; then
  echo "The directory containing the epa Postgres dump files to load is not defined."
  exit 2
fi

# used by psql & pg_restore
export PGPASSWORD=$EPA_DB_OWNER_PASSWORD

# clear out the old tables
echo "Deleting old wqx_dump tables..."
echo "select wqx_dump.drop_tables();" > $EPA_WQX_DUMP_DIR//drop_wqx_dump_tables.sql
psql -h $DB_ADDRESS -U $EPA_SCHEMA_OWNER_USERNAME \
     -d $EPA_DATABASE_NAME -p $DATABASE_PORT \
     -f $EPA_WQX_DUMP_DIR/drop_wqx_dump_tables.sql

# load the files
echo "Loading eqp wqx dump files into address=$DB_ADDRESS, port==$DATABASE_PORT, user=$EPA_SCHEMA_OWNER_USERNAME"
for file in $EPA_WQX_DUMP_DIR/*.dump; do 
   echo "Loading $file..."

   pg_restore --host $DB_ADDRESS --port=$DATABASE_PORT --username=$EPA_SCHEMA_OWNER_USERNAME \
             --data-only --dbname=$EPA_DATABASE_NAME --dbname=dbname= --schema=wqx_dump
             --no-privileges  $dump_file
done

