#!/bin/sh
set -eu

mkdir -p backups
stamp=$(date +%Y%m%d-%H%M%S)

echo "Creating SQLite backup..."
docker compose exec -T web python -c '
import os
import sqlite3
import sys
import tempfile

source = sqlite3.connect(os.environ.get("SQLITE_DATABASE_PATH", "/app/data/db.sqlite3"))
with tempfile.NamedTemporaryFile() as backup_file:
    target = sqlite3.connect(backup_file.name)
    source.backup(target)
    target.close()
    backup_file.seek(0)
    sys.stdout.buffer.write(backup_file.read())
source.close()
' > "backups/db-$stamp.sqlite3"

echo "Creating media backup..."
docker compose exec -T web tar czf - -C /app/data/media . > "backups/media-$stamp.tar.gz"

echo "Backup completed: $stamp"
echo "  backups/db-$stamp.sqlite3"
echo "  backups/media-$stamp.tar.gz"
