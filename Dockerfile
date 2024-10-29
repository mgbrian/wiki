FROM python:3.11-alpine

WORKDIR /app

COPY . /app

RUN apk update && apk add --no-cache curl libmagic
RUN curl -fsSL https://ollama.com/install.sh | sh

RUN chmod +x install.sh && ./install.sh

# Update env.py
RUN FLASK_SECRET_KEY=$(openssl rand -base64 15 | tr -dc 'a-zA-Z0-9') && \
    DJANGO_SECRET_KEY=$(openssl rand -base64 15 | tr -dc 'a-zA-Z0-9') && \
    echo "os.environ.setdefault('FLASK_SECRET_KEY', '${FLASK_SECRET_KEY}')" >> /app/env.py && \
    echo "os.environ.setdefault('DJANGO_SECRET_KEY', '${DJANGO_SECRET_KEY}')" >> /app/env.py && \
    echo "os.environ.setdefault('POSTGRES_DB_NAME', os.getenv('POSTGRES_DB', 'default_db'))" >> /app/env.py && \
    echo "os.environ.setdefault('POSTGRES_DB_USER', os.getenv('POSTGRES_USER', 'default_user'))" >> /app/env.py && \
    echo "os.environ.setdefault('POSTGRES_DB_PASSWORD', os.getenv('POSTGRES_PASSWORD', ''))" >> /app/env.py && \
    echo "os.environ.setdefault('POSTGRES_HOST', 'db')" >> /app/env.py && \
    echo "os.environ.setdefault('POSTGRES_PORT', '5432')" >> /app/env.py

# Apply database migrations
RUN source .requirements/bin/activate && python  manage.py migrate

# Make port 5000 available to the world outside this container
EXPOSE 5000

CMD ["hypercorn", "--workers=3", "--bind", "0.0.0.0:5000", "app:app"]
