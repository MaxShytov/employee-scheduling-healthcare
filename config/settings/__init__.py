"""
Django settings loader.
Loads appropriate settings based on DJANGO_SETTINGS_MODULE environment variable.
"""

import os

# Default to development settings
SETTINGS_MODULE = os.environ.get('DJANGO_SETTINGS_MODULE', 'config.settings.development')

if SETTINGS_MODULE == 'config.settings.development':
    from .development import *
elif SETTINGS_MODULE == 'config.settings.production':
    from .production import *
else:
    from .base import *