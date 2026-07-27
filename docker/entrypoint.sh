#!/bin/sh
set -eu

fail() {
  echo "ERROR: $1" >&2
  exit 1
}

is_placeholder() {
  case "${1:-}" in
    ""|replace-*|ChangeMe*|change-me*) return 0 ;;
    *) return 1 ;;
  esac
}

# Refuse to start a production-mode container with the sample credentials.
if [ "${DJANGO_DEBUG:-False}" != "True" ]; then
  is_placeholder "${DJANGO_SECRET_KEY:-}" && fail "Set a strong DJANGO_SECRET_KEY in .env."
  is_placeholder "${MYSQL_PASSWORD:-}" && fail "Replace the sample MYSQL_PASSWORD in .env."
  is_placeholder "${MYSQL_ROOT_PASSWORD:-}" && fail "Replace the sample MYSQL_ROOT_PASSWORD in .env."
  if [ "${AUTO_BOOTSTRAP:-True}" = "True" ]; then
    is_placeholder "${DJANGO_SUPERUSER_PASSWORD:-}" && fail "Replace the sample DJANGO_SUPERUSER_PASSWORD in .env."
  fi
fi

if [ -n "${MYSQL_HOST:-}" ]; then
  echo "Waiting for MySQL at ${MYSQL_HOST}:${MYSQL_PORT:-3306}..."
  until nc -z "$MYSQL_HOST" "${MYSQL_PORT:-3306}"; do sleep 2; done
fi

python manage.py migrate --noinput
python manage.py collectstatic --noinput
if [ "${AUTO_BOOTSTRAP:-True}" = "True" ]; then
  if [ "${LOAD_DEMO_DATA:-False}" = "True" ]; then
    python manage.py bootstrap_system
  else
    python manage.py bootstrap_system --no-demo
  fi
fi
exec "$@"
