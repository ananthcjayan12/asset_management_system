#!/bin/sh
set -eu

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 backups/db-YYYYMMDD-HHMMSS.sql.gz" >&2
  exit 2
fi

printf 'This replaces data in the configured MySQL database. Type RESTORE to continue: '
read answer
[ "$answer" = "RESTORE" ] || { echo "Cancelled."; exit 1; }

gzip -dc "$1" | docker compose exec -T db sh -c 'mysql -uroot -p"$MYSQL_ROOT_PASSWORD" "$MYSQL_DATABASE"'
echo "Database restore completed."
