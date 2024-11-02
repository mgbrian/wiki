FROM python:3.11-alpine

WORKDIR /app

RUN apk update && apk add --no-cache curl libmagic openssl

# Use Ollama Docker container instead.
# RUN curl -fsSL https://ollama.com/install.sh | sh

# Enable sudo
# https://stackoverflow.com/questions/49225976/use-sudo-inside-dockerfile-alpine
RUN set -ex && apk --no-cache add sudo

COPY . /app

RUN chmod +x install.sh && sh install.sh

# Update env.py. First addition to env.py overwrites whatever install.sh put into it.
RUN FLASK_SECRET_KEY=$(openssl rand -base64 15 | tr -dc 'a-zA-Z0-9') && \
    DJANGO_SECRET_KEY=$(openssl rand -base64 15 | tr -dc 'a-zA-Z0-9') && \
    echo "import os" > env.py && \
    echo "os.environ.setdefault('FLASK_SECRET_KEY', '${FLASK_SECRET_KEY}')" >> env.py && \
    echo "os.environ.setdefault('DJANGO_SECRET_KEY', '${DJANGO_SECRET_KEY}')" >> env.py && \
    echo "os.environ.setdefault('POSTGRES_DB_NAME', os.getenv('POSTGRES_DB', 'default_db'))" >> env.py && \
    echo "os.environ.setdefault('POSTGRES_DB_USER', os.getenv('POSTGRES_USER', 'default_user'))" >> env.py && \
    echo "os.environ.setdefault('POSTGRES_DB_PASSWORD', os.getenv('POSTGRES_PASSWORD', ''))" >> env.py && \
    echo "os.environ.setdefault('POSTGRES_HOST', 'db')" >> env.py && \
    echo "os.environ.setdefault('POSTGRES_PORT', '5432')" >> env.py && \
    echo "os.environ.setdefault('GOOGLE_API_KEY', os.getenv('GOOGLE_API_KEY', ''))" >> env.py && \
    echo "os.environ.setdefault('OPENAI_API_KEY', os.getenv('OPENAI_API_KEY', ''))" >> env.py && \
    echo "os.environ.setdefault('GROQ_API_KEY', os.getenv('GROQ_API_KEY', ''))" >> env.py && \
    echo "os.environ.setdefault('OLLAMA_CLIENT_HOST', 'http://ollama:11434')" >> env.py

# Apply database migrations
#RUN  .requirements/bin/python manage.py migrate

# TODO: Add this to deployment instructions for the benefit of bare-metal Linux deployments.
# Also see GPU considerations here:
# https://github.com/ollama/ollama/blob/main/docs/linux.md
#RUN ollama serve

# Make port 5000 available to the world outside this container
EXPOSE 5000

RUN chmod +x start.sh
CMD ["/app/start.sh"]
#CMD ["/app/.requirements/bin/hypercorn", "--workers=3", "--bind", "0.0.0.0:5000", "app:app"]
#CMD ["/app/.requirements/bin/python", "/app/manage.py", "migrate"]
