"""Use this to create an env.py and populate the variables below."""
import os

# Set this to a long random sting
os.environ.setdefault('FLASK_SECRET_KEY', '')

# API key for Gemini.
os.environ.setdefault('GOOGLE_API_KEY', '')

# DB settings.
# Set Django secret key to a long random string.
os.environ.setdefault('DJANGO_SECRET_KEY', '')
os.environ.setdefault('POSTGRES_DB_NAME', '')
os.environ.setdefault('POSTGRES_DB_USER', '')
os.environ.setdefault('POSTGRES_DB_PASSWORD', '')
os.environ.setdefault('POSTGRES_HOST', '')
os.environ.setdefault('POSTGRES_PORT', '')
