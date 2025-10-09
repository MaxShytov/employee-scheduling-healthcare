"""
Custom template tags for the core app.
"""

from django import template
from django.utils.html import format_html
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def format_hours(hours):
    """Format hours as human-readable string."""
    if not hours:
        return "0h"
    
    full_hours = int(hours)
    minutes = int((hours - full_hours) * 60)
    
    if minutes > 0:
        return f"{full_hours}h {minutes}m"
    return f"{full_hours}h"


@register.simple_tag
def badge(text, style='primary'):
    """
    Render a Bootstrap badge.
    
    Usage: {% badge "Active" "success" %}
    """
    return format_html(
        '<span class="badge bg-{}">{}</span>',
        style,
        text
    )


@register.filter
def status_badge(status):
    """
    Convert status to colored badge.
    
    Usage: {{ object.status|status_badge }}
    """
    status_map = {
        'active': 'success',
        'pending': 'warning',
        'inactive': 'secondary',
        'approved': 'success',
        'rejected': 'danger',
        'draft': 'secondary',
    }
    
    style = status_map.get(status.lower(), 'primary')
    return format_html(
        '<span class="badge bg-{}">{}</span>',
        style,
        status.title()
    )