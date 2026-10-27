#!/bin/bash
set -e

echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "Loading reference data..."
python manage.py loaddata groups.json statuses.json object_types.json

if [ "${LOAD_DEMO_DATA:-false}" = "true" ]; then
    echo "Loading demo data (demo users, customers, work catalog)..."
    python manage.py loaddata users.json dental_lab_data.json
fi

echo "Starting server..."
exec "$@"
