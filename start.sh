#!/bin/sh

# Differentiate between Docker/ local dev setups.
if [ -d "/app/.requirements" ]; then
    source /app/.requirements/bin/activate
else
    source .requirements/bin/activate
fi

python manage.py migrate

hypercorn --workers=3 --bind 0.0.0.0:5000 app:app
