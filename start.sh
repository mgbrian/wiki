#!/bin/sh

if [ -d "/app" ]; then
    RUNNING_ON_DOCKER=true
else
    RUNNING_ON_DOCKER=false
fi

if [ "$RUNNING_ON_DOCKER" = true ]; then
    LOG_DIR="/var/log"
else
    LOG_DIR="./log"
fi

# Create log directory if it doesn't exist.
if [ ! -d "$LOG_DIR" ]; then
    mkdir -p "$LOG_DIR"
    echo "Log directory '$LOG_DIR' created."
fi

# Set DEBUG to 0 if not already defined.
export DEBUG=${DEBUG:-0}

if [ "$RUNNING_ON_DOCKER" = true ]; then
    # Create media folder if it doesn't exist.
    if [ ! -d "/app/media" ]; then
        mkdir -p /app/media
        echo "Folder 'media' created."
    fi

    source /app/.requirements/bin/activate
else
    if [ ! -d "media" ]; then
        mkdir -p media
        echo "Folder 'media' created."
    fi

    source .requirements/bin/activate
fi

# Pull models and apply migrations.
if [ -f "dependencies/models.txt" ]; then
    while IFS= read -r model; do
        echo "Pulling $model..."
        python -c "from llm.apis import OllamaAPI; OllamaAPI().pull_model('$model')"
    done < dependencies/models.txt
fi

python manage.py migrate

# Start Hypercorn with different logging configurations based on DEBUG mode.
if [ "$DEBUG" = "1" ]; then
    echo "\nServer running in DEBUG mode. Set the DEBUG environment variable to 0 in production!\n"
    hypercorn --log-level DEBUG --access-logfile - --workers=3 --bind 0.0.0.0:5000 app:app
else
    hypercorn --log-level WARNING --access-logfile "$LOG_DIR/hypercorn_access.log" --error-logfile "$LOG_DIR/hypercorn_error.log" --workers=3 --bind 0.0.0.0:5000 app:app
fi
