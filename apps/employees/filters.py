# apps/employees/filters.py
from django.utils.translation import gettext_lazy as _
from apps.core.filters import FilterSet, TextFilter, ChoiceFilter, BooleanFilter
from apps.employees.models import Location, Position, Department


class EmployeeFilterSet(FilterSet):
    """Filters for Employee list"""
    
    search = TextFilter(
        field_name='user__first_name',
        label=_('Search'),
        placeholder=_('Search by name...')
    )
    
    location = ChoiceFilter(
        field_name='location',
        label=_('Location'),
        queryset=Location.objects.filter(is_active=True).order_by('name'),
        empty_label=_('All locations')
    )
    
    position = ChoiceFilter(
        field_name='position',
        label=_('Position'),
        queryset=Position.objects.filter(is_active=True).order_by('title'),
        empty_label=_('All positions')
    )
    
    department = ChoiceFilter(
        field_name='department',
        label=_('Department'),
        queryset=Department.objects.filter(is_active=True).order_by('name'),
        empty_label=_('All departments')
    )
    
    is_active = BooleanFilter(
        field_name='is_active',
        label=_('Active only')
    )


class PositionFilterSet(FilterSet):
    """Filters for Position list"""
    
    search = TextFilter(
        field_name='title',  # ИСПРАВЛЕНО: Position uses 'title'
        label=_('Search'),
        placeholder=_('Search positions...')
    )
    
    requires_certification = BooleanFilter(
        field_name='requires_certification',
        label=_('Requires certification')
    )
    
    is_active = BooleanFilter(
        field_name='is_active',
        label=_('Active only')
    )


class LocationFilterSet(FilterSet):
    """Filters for Location list"""
    
    search = TextFilter(
        field_name='name',
        label=_('Search'),
        placeholder=_('Search locations...')
    )
    
    city = TextFilter(
        field_name='city',
        label=_('City'),
        placeholder=_('Filter by city...')
    )
    
    is_active = BooleanFilter(
        field_name='is_active',
        label=_('Active only')
    )


class DepartmentFilterSet(FilterSet):
    """Filters for Department list"""
    
    search = TextFilter(
        field_name='name',
        label=_('Search'),
        placeholder=_('Search departments...')
    )
    
    is_active = BooleanFilter(
        field_name='is_active',
        label=_('Active only')
    )