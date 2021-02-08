#!/bin/bash
# The set -e tells bash to exit immediately if a simple command fails.
# The set -o pipefail tells bash to set pipeline's return status to status of the last (rightmost) command.
set -e
set -o pipefail

# This script loads epa Postgres wqx dump files into the wqx_schema
# Enviroment variables needed:
# EPA_DATABASE_ADDRESS  -- Host name or IP address of the PostgreSQL database.
# EPA_SCHEMA_OWNER_USERNAME -- Role which owns the **WQX_SCHEMA_NAME** and **STORETW_SCHEMA_NAME** database objects.
# EPA_SCHEMA_OWNER_PASSWORD --  Password for the **EPA_SCHEMA_OWNER_USERNAME** role.
# EPA_DATABASE_NAME -- Name of the PostgreSQL database containing the wqx_dump schema.
# EPA_WQX_DUMP_DIR  -- directory where the Postgresq pg_dump archive files are located

# Optional DATABASE_PORT defaults to 5432
if [ -z "$DATABASE_PORT" ]; then
  export DATABASE_PORT=5432
fi

export PATH=/mingw64/bin:$PATH

if [ -z "$EPA_DATABASE_ADDRESS" ]; then
  echo "The Postgres server (EPA_DATABASE_ADDRESS) to connect to is not defined."
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

if [ -z "$EPA_DATABASE_NAME" ]; then
  echo "The database name (EPA_DATABASE_NAME) to restore into is not defined."
  exit 2
fi

if [ -z "$EPA_WQX_DUMP_DIR" ]; then
  echo "The directory containing the epa Postgres dump files to load is not defined."
  exit 2
fi

# used by psql & pg_restore
export PGPASSWORD=$EPA_SCHEMA_OWNER_PASSWORD

# clear out the old tables
echo "Deleting old wqx_dump tables..."
echo "select wqx_dump.drop_tables();" > $EPA_WQX_DUMP_DIR//drop_wqx_dump_tables.sql
psql -h $EPA_DATABASE_ADDRESS -U $EPA_SCHEMA_OWNER_USERNAME \
     -d $EPA_DATABASE_NAME -p $DATABASE_PORT \
     -f $EPA_WQX_DUMP_DIR/drop_wqx_dump_tables.sql

# load the files
echo "Loading epa wqx dump files into address=$EPA_DATABASE_ADDRESS, port==$DATABASE_PORT, user=$EPA_SCHEMA_OWNER_USERNAME"
for dump_file in $EPA_WQX_DUMP_DIR/*.dump; do
   echo "Loading $dump_file ..."

   pg_restore -v --host $EPA_DATABASE_ADDRESS --port=$DATABASE_PORT --username=$EPA_SCHEMA_OWNER_USERNAME \
             --dbname=$EPA_DATABASE_NAME --schema=wqx_dump --no-privileges --no-owner $dump_file
done

