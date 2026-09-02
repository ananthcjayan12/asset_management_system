#!/bin/sh
set -eu

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 backups/db-YYYYMMDD-HHMMSS.sqlite3" >&2
  exit 2
fi

printf 'This replaces data in the configured SQLite database. Type RESTORE to continue: '
read answer
[ "$answer" = "RESTORE" ] || { echo "Cancelled."; exit 1; }

docker compose cp "$1" web:/tmp/asset-management-restore.sqlite3
docker compose exec -T web python -c '
import os
import sqlite3

source = sqlite3.connect("/tmp/asset-management-restore.sqlite3")
target = sqlite3.connect(os.environ.get("SQLITE_DATABASE_PATH", "/app/data/db.sqlite3"))
source.backup(target)
target.close()
source.close()
'
docker compose exec -T web rm -f /tmp/asset-management-restore.sqlite3
docker compose restart web
echo "Database restore completed."
