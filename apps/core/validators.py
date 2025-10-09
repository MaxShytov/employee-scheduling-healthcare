"""
Custom validators for the application.
"""

from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import re


def validate_swiss_phone(value):
    """
    Validate Swiss phone number format.
    Accepts: +41 XX XXX XX XX or 0XX XXX XX XX
    """
    # Remove spaces and common separators
    clean_value = re.sub(r'[\s\-\(\)]', '', value)
    
    # Swiss phone patterns
    patterns = [
        r'^\+41\d{9}$',  # +41XXXXXXXXX
        r'^0\d{9}$',      # 0XXXXXXXXX
    ]
    
    if not any(re.match(pattern, clean_value) for pattern in patterns):
        raise ValidationError(
            _('Enter a valid Swiss phone number (e.g., +41 XX XXX XX XX or 0XX XXX XX XX)'),
            code='invalid'
        )


def validate_swiss_postal_code(value):
    """
    Validate Swiss postal code (4 digits).
    """
    if not re.match(r'^\d{4}$', value):
        raise ValidationError(
            _('Swiss postal code must be exactly 4 digits'),
            code='invalid'
        )