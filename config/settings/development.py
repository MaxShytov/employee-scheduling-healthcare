"""
Development settings for MedShift Scheduler.
"""

from .base import *

DEBUG = True

# Development-specific apps
INSTALLED_APPS += [
    'debug_toolbar',
]

MIDDLEWARE += [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

# Django Debug Toolbar
INTERNAL_IPS = [
    '127.0.0.1',
]

# Email backend for development (console)
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Disable password validators in development
AUTH_PASSWORD_VALIDATORS = []

# Allow all origins in development
CORS_ALLOW_ALL_ORIGINS = True