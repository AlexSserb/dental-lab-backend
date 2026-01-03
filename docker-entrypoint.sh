#!/bin/bash
set -e

echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "Loading default data..."
python manage.py loaddata groups.json users.json statuses.json object_types.json dental_lab_data.json

echo "Starting server..."
exec "$@"
