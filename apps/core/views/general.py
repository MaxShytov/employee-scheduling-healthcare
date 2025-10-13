# apps/core/views/general.py
"""
Core views.
"""

import os
from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.conf import settings


@login_required
def help_page(request):
    """Help and documentation page."""
    
    # Check if PDF files exist
    user_manual_exists = os.path.exists(
        os.path.join(settings.STATIC_ROOT or settings.BASE_DIR / 'static', 'docs', 'USER_MANUAL.pdf')
    )
    quick_start_exists = os.path.exists(
        os.path.join(settings.STATIC_ROOT or settings.BASE_DIR / 'static', 'docs', 'QUICK_START.pdf')
    )
    
    return render(request, 'core/help.html', {
        'page_title': 'Help & Documentation',
        'user_manual_exists': user_manual_exists,
        'quick_start_exists': quick_start_exists,
    })