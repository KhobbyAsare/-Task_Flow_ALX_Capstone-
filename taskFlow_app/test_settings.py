"""
Test settings for Django project - uses SQLite for faster testing
"""

from .settings import *

# Use SQLite for testing to avoid remote database connection issues
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',  # In-memory database for faster tests
    }
}

# Disable migrations for faster test setup
class DisableMigrations:
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None

# Comment out the line below if you want to run full migrations during testing
MIGRATION_MODULES = DisableMigrations()

# Faster password hashing for tests
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.MD5PasswordHasher',
]

# Disable debug for tests
DEBUG = False

# Minimal logging for tests
LOGGING_CONFIG = None
