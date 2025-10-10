"""
Dashboard views.
"""

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _

from apps.employees.models import Employee, Department, Position


@login_required
def home(request):
    """
    Dashboard home page.
    """
    
    # Get statistics
    total_employees = Employee.objects.filter(is_active=True).count()
    total_departments = Department.objects.filter(is_active=True).count()
    total_positions = Position.objects.filter(is_active=True).count()
    
    # TODO: When shifts are implemented
    today_shifts = 0
    active_now = 0
    
    # TODO: When certifications are implemented
    total_certifications = 0
    
    context = {
        'page_title': _('Dashboard'),
        'user': request.user,
        'total_employees': total_employees,
        'total_departments': total_departments,
        'total_positions': total_positions,
        'today_shifts': today_shifts,
        'active_now': active_now,
        'total_certifications': total_certifications,
    }
    return render(request, 'dashboard/home.html', context)