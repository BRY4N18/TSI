#!/bin/bash
# Se ejecuta solo en el primer arranque (volumen vacío).
# Crea la base analítica del stack tactico — nombre desde CLICKHOUSE_DB.
set -euo pipefail
DB="${CLICKHOUSE_DB:-tsi_tactico}"
USER="${CLICKHOUSE_USER:-tactico}"
PASS="${CLICKHOUSE_PASSWORD:-tactico}"
clickhouse-client --user "$USER" --password "$PASS" --query "CREATE DATABASE IF NOT EXISTS ${DB}"
echo "ClickHouse database ready: ${DB}"
