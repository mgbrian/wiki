#!/bin/sh

# Set DEBUG to 0 if not already defined.
export DEBUG=${DEBUG:-0}

# The IF part => Running in Docker Container; ELSE part => Bare Metal.
if [ -d "/app" ]; then
    LOG_DIR="/var/log"
    MEDIA_DIR="/app/media"
    VENV_DIR="/app/.requirements"
else
    LOG_DIR="./log"
    MEDIA_DIR="./media"
    VENV_DIR=".requirements"
fi

# Create log directory if it doesn't exist.
if [ ! -d "$LOG_DIR" ]; then
    mkdir -p "$LOG_DIR"
    echo "Log directory '$LOG_DIR' created."
fi

# Create media folder if it doesn't exist.
if [ ! -d "$MEDIA_DIR" ]; then
    mkdir -p "$MEDIA_DIR"
    echo "'media' folder created at $MEDIA_DIR."
fi

source "$VENV_DIR"/bin/activate

# Pull Ollama models.
if [ -f "dependencies/models.txt" ]; then
    while IFS= read -r model; do
        echo "Pulling $model..."
        python -c "from llm.apis import OllamaAPI; OllamaAPI().pull_model('$model')"
    done < dependencies/models.txt
fi

 # Apply db migrations.
python manage.py migrate

# Start Hypercorn with different logging configurations based on DEBUG flag.
if [ "$DEBUG" = "1" ]; then
    echo "\nServer running in DEBUG mode. Set the DEBUG environment variable to 0 in production!\n"
    hypercorn --log-level DEBUG --access-logfile - --workers=3 --bind 0.0.0.0:5000 app:app
else
    hypercorn --log-level WARNING --access-logfile "$LOG_DIR/hypercorn_access.log" --error-logfile "$LOG_DIR/hypercorn_error.log" --workers=3 --bind 0.0.0.0:5000 app:app
fi
