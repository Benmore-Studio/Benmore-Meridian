"""
Django Development Settings
Settings specific to local development environment
"""

from .base import *  # noqa: F403

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Allow all hosts in development
ALLOWED_HOSTS = ["*"]

# Development-specific installed apps
INSTALLED_APPS += [  # noqa: F405
    "django_extensions",  # Useful dev tools (shell_plus, etc.)
    "debug_toolbar",  # Django Debug Toolbar
]

MIDDLEWARE += [  # noqa: F405
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]

# Internal IPs for Django Debug Toolbar
INTERNAL_IPS = [
    "127.0.0.1",
    "localhost",
]

# Django Debug Toolbar Configuration
DEBUG_TOOLBAR_CONFIG = {
    "SHOW_TOOLBAR_CALLBACK": lambda request: DEBUG,  # noqa: F405
}

# Email backend for development (console output)
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"

# Django REST Framework - Add browsable API renderer in dev
REST_FRAMEWORK["DEFAULT_RENDERER_CLASSES"] = [  # noqa: F405
    "rest_framework.renderers.JSONRenderer",
    "rest_framework.renderers.BrowsableAPIRenderer",  # Enable browsable API
]

# Disable password validation in development for easier testing
AUTH_PASSWORD_VALIDATORS = []  # noqa: F405

# CORS - Allow all origins in development
CORS_ALLOW_ALL_ORIGINS = True

# Logging - More verbose in development
LOGGING["handlers"]["console"]["level"] = "DEBUG"  # noqa: F405
LOGGING["root"]["level"] = "DEBUG"  # noqa: F405
