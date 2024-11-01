#!/bin/sh
source /app/.requirements/bin/activate

python manage.py migrate

hypercorn --workers=3 --bind 0.0.0.0:5000 app:app
