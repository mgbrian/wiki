#!/bin/sh

# Differentiate between Docker/ local dev setups.
if [ -d "/app/.requirements" ]; then
    # Create media folder if it doesn't exist.
    if [ ! -d "/app/media" ]; then
        mkdir /app/media
        echo "Folder 'media' created."
    fi

    source /app/.requirements/bin/activate
else
    if [ ! -d "media" ]; then
        mkdir media
        echo "Folder 'media' created."
    fi

    source .requirements/bin/activate
fi

# TODO: Do this more dynamically.
python -c "from llm.apis import OllamaAPI; OllamaAPI().pull_model('nomic-embed-text')"
python manage.py migrate

# Log verbosely to the terminal in DEBUG mode
if [[ "$DEBUG" == "1" ]]; then
    hypercorn --log-level DEBUG --access-logfile - --workers=3 --bind 0.0.0.0:5000 app:app
else
    # Log silently to a file
    hypercorn --log-level WARNING --access-logfile /var/log/hypercorn_access.log --error-logfile /var/log/hypercorn_error.log --workers=3 --bind 0.0.0.0:5000 app:app
fi
# hypercorn --workers=3 --bind 0.0.0.0:5000 app:app
