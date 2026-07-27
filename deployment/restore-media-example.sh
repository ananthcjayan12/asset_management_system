#!/bin/sh
set -eu

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 backups/media-YYYYMMDD-HHMMSS.tar.gz" >&2
  exit 2
fi

printf 'This replaces files in the configured media volume. Type RESTORE to continue: '
read answer
[ "$answer" = "RESTORE" ] || { echo "Cancelled."; exit 1; }

docker compose exec -T web sh -c 'find /app/media -mindepth 1 -delete'
docker compose exec -T web tar xzf - -C /app/media < "$1"
echo "Media restore completed."
