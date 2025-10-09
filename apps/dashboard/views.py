"""
Dashboard views.
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _


@login_required
def home(request):
    """
    Dashboard home page.
    """
    context = {
        'page_title': _('Dashboard'),
        'user': request.user,
    }
    return render(request, 'dashboard/home.html', context)