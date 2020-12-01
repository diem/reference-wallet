#!/bin/bash

# Copyright (c) The Diem Core Contributors
# SPDX-License-Identifier: Apache-2.0

set -e

LP_DB_NAME="liquidity_provider_db"
DB_NAME="backend_db"
DB_USER="backenduser"
DB_PASSWORD="backendpassword"

psql -v ON_ERROR_STOP=0 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
    CREATE DATABASE $DB_NAME;
    GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;
EOSQL

psql -v ON_ERROR_STOP=0 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
    CREATE DATABASE $LP_DB_NAME;
    GRANT ALL PRIVILEGES ON DATABASE $LP_DB_NAME TO $DB_USER;
EOSQL
