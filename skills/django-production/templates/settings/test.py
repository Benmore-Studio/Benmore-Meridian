"""
Django Test Settings
Fast, isolated configuration for running tests
"""

from .base import *  # noqa: F403

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = "django-insecure-test-key-not-for-production"  # noqa: S105

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# Test database - Use in-memory SQLite for speed
DATABASES = {  # noqa: F405
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

# Faster password hashing for tests
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

# Disable migrations for faster tests
class DisableMigrations:
    def __contains__(self, item):
        return True

    def __getitem__(self, item):
        return None


MIGRATION_MODULES = DisableMigrations()

# Email backend for tests
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# Cache - Use local memory cache for tests
CACHES = {  # noqa: F405
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    }
}

# Logging - Minimal logging in tests
LOGGING = {  # noqa: F405
    "version": 1,
    "disable_existing_loggers": True,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "level": "CRITICAL",
        "handlers": ["console"],
    },
}

# CORS - Allow all origins in tests
CORS_ALLOW_ALL_ORIGINS = True

# Celery - Use synchronous mode for tests (if using Celery)
# CELERY_TASK_ALWAYS_EAGER = True
# CELERY_TASK_EAGER_PROPAGATES = True
