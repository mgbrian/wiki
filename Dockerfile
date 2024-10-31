FROM python:3.11-alpine

WORKDIR /app

RUN apk update && apk add --no-cache curl libmagic

RUN curl -fsSL https://ollama.com/install.sh | sh

# Enable sudo
# https://stackoverflow.com/questions/49225976/use-sudo-inside-dockerfile-alpine
RUN set -ex && apk --no-cache add sudo

COPY . /app

RUN chmod +x install.sh && sh install.sh

# Update env.py
RUN FLASK_SECRET_KEY=$(openssl rand -base64 15 | tr -dc 'a-zA-Z0-9') && \
    DJANGO_SECRET_KEY=$(openssl rand -base64 15 | tr -dc 'a-zA-Z0-9') && \
    echo "os.environ.setdefault('FLASK_SECRET_KEY', '${FLASK_SECRET_KEY}')" >> env.py && \
    echo "os.environ.setdefault('DJANGO_SECRET_KEY', '${DJANGO_SECRET_KEY}')" >> env.py && \
    echo "os.environ.setdefault('POSTGRES_DB_NAME', os.getenv('POSTGRES_DB', 'default_db'))" >> env.py && \
    echo "os.environ.setdefault('POSTGRES_DB_USER', os.getenv('POSTGRES_USER', 'default_user'))" >> env.py && \
    echo "os.environ.setdefault('POSTGRES_DB_PASSWORD', os.getenv('POSTGRES_PASSWORD', ''))" >> env.py && \
    echo "os.environ.setdefault('POSTGRES_HOST', 'db')" >> env.py && \
    echo "os.environ.setdefault('POSTGRES_PORT', '5432')" >> env.py

# Apply database migrations
RUN source .requirements/bin/activate && python manage.py migrate

# TODO: Add this to deployment instructions for the benefit of bare-metal Linux deployments.
# Also see GPU considerations here:
# https://github.com/ollama/ollama/blob/main/docs/linux.md
RUN ollama serve

# Make port 5000 available to the world outside this container
EXPOSE 5000

CMD ["hypercorn", "--workers=3", "--bind", "0.0.0.0:5000", "app:app"]
