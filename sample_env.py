"""Use this to create an env.py and populate the variables below."""
import os


os.environ.setdefault('FLASK_SECRET_KEY', '')

# DB settings.
os.environ.setdefault('DJANGO_SECRET_KEY', '')
os.environ.setdefault('POSTGRES_DB_NAME', '')
os.environ.setdefault('POSTGRES_DB_USER', '')
os.environ.setdefault('POSTGRES_DB_PASSWORD', '')
os.environ.setdefault('POSTGRES_HOST', '')
os.environ.setdefault('POSTGRES_PORT', '')
