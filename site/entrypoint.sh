set -e

mkdir -p /data /app/ITRexHelper/media /app/ITRexHelper/staticfiles

python manage.py migrate --noinput
python manage.py collectstatic --noinput

exec "$@"
