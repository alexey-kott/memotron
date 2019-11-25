#!/bin/bash
set -e

psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname postgres <<-EOSQL
    CREATE USER memotron_bot;
    CREATE DATABASE memotron;
    GRANT ALL PRIVILEGES ON DATABASE memotron TO memotron_bot;
EOSQL