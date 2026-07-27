#!/bin/sh
set -eu

mkdir -p backups
stamp=$(date +%Y%m%d-%H%M%S)

echo "Creating MySQL backup..."
docker compose exec -T db sh -c 'mysqldump --single-transaction --routines --triggers -uroot -p"$MYSQL_ROOT_PASSWORD" "$MYSQL_DATABASE"' \
  | gzip > "backups/db-$stamp.sql.gz"

echo "Creating media backup..."
docker compose exec -T web tar czf - -C /app/media . > "backups/media-$stamp.tar.gz"

echo "Backup completed: $stamp"
echo "  backups/db-$stamp.sql.gz"
echo "  backups/media-$stamp.tar.gz"
