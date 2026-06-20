#!/bin/sh
set -e

cd /app/ITRexHelper

mkdir -p /data /app/ITRexHelper/staticfiles /app/ITRexHelper/media

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec "$@"
