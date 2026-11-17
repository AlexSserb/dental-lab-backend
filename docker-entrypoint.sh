#!/bin/bash
set -e

echo "Generating migrations for model changes (if any)..."
python manage.py makemigrations --noinput

echo "Applying database migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

echo "Loading reference data..."
python manage.py loaddata groups.json statuses.json object_types.json

if [ "${LOAD_DEMO_DATA:-false}" = "true" ]; then
    echo "Loading demo data (demo users, customers, work catalog)..."
    python manage.py loaddata users.json dental_lab_data.json
    # Defect triage demo: orders, works, operations, closed cases (with embeddings) and triages
    # in the submitted / applied / dismissed / failed states. The worker turns the submitted ones
    # into real awaiting-review rows with LLM proposals on its first polls.
    python manage.py loaddata defects_demo.json
fi

echo "Starting server..."
exec "$@"
