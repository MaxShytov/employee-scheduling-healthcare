# apps/employees/filters.py
from django.utils.translation import gettext_lazy as _
from apps.core.filters import FilterSet, TextFilter, ChoiceFilter, BooleanFilter
from apps.employees.models import Location, Position, Department
from django.db.models import Q


class EmployeeFilterSet(FilterSet):
    """Filters for Employee list"""
    
    is_active = BooleanFilter(
        field_name='is_active',
        label=_('Status'),
        as_buttons=True
    )
    
    search = TextFilter(
        field_name='user__first_name',  # Основное поле (для обратной совместимости)
        label=_('Search'),
        placeholder=_('Search by name...'),
        search_fields=[  # ← Новое: список полей для поиска
            'user__first_name',
            'user__last_name',
            'user__email',
            'employee_id'
        ]
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

class PositionFilterSet(FilterSet):
    """Filters for Position list"""

    is_active = BooleanFilter(
        field_name='is_active',
        label=_('Status'),
        as_buttons=True
    )

    search = TextFilter(
        field_name='title',
        label=_('Search'),
        placeholder=_('Search by title or code...'),
        search_fields=['title', 'code', 'description']
    )

    requires_certification = BooleanFilter(
        field_name='requires_certification',
        label=_('Certification'),
        as_buttons=True,
        true_label=_('Required'),
        false_label=_('Not Required'),
        true_color='warning',
        false_color='secondary'
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


# apps/employees/filters.py

class DepartmentFilterSet(FilterSet):
    """Filters for Department list"""
   
    is_active = BooleanFilter(
        field_name='is_active',
        label=_('Status'),
        as_buttons=True
    )   
    
    search = TextFilter(
        field_name='name',
        label=_('Search'),
        placeholder=_('Search by name or code...'),
        search_fields=['name', 'code', 'description']
    )
    
    has_manager = ChoiceFilter(
        field_name='manager',
        label=_('Manager'),
        choices=[
            ('', _('All')),
            ('yes', _('Has Manager')),
            ('no', _('No Manager'))
        ],
        empty_label=None,
        lookup='isnull'  # Special lookup for null checks
    )
    
    def apply_filters(self, queryset):
        """
        Apply filters to queryset.
        English: Override to handle special 'has_manager' filter logic.
        """
        # English: First apply standard filters from parent
        for name, filter_obj in self.filters.items():
            # Skip has_manager, we'll handle it separately
            if name == 'has_manager':
                continue
                
            filter_kwargs = filter_obj.get_filter_kwargs()
            if filter_kwargs:
                if '__q' in filter_kwargs:
                    queryset = queryset.filter(filter_kwargs['__q'])
                else:
                    queryset = queryset.filter(**filter_kwargs)
        
        # English: Handle has_manager special logic
        has_manager_filter = self.filters.get('has_manager')
        if has_manager_filter and has_manager_filter.value:
            if has_manager_filter.value == 'yes':
                queryset = queryset.filter(manager__isnull=False)
            elif has_manager_filter.value == 'no':
                queryset = queryset.filter(manager__isnull=True)

        return queryset


class LocationFilterSet(FilterSet):
    """Filters for Location list"""

    is_active = BooleanFilter(
        field_name='is_active',
        label=_('Status'),
        as_buttons=True
    )

    search = TextFilter(
        field_name='name',
        label=_('Search'),
        placeholder=_('Search by name, city, or address...'),
        search_fields=['name', 'code', 'city', 'address']
    )

    country = ChoiceFilter(
        field_name='country',
        label=_('Country'),
        choices=[
            ('', _('All Countries')),
            ('CH', _('Switzerland')),
            ('CA', _('Canada')),
            ('LU', _('Luxembourg')),
            ('MC', _('Monaco'))
        ],
        empty_label=None
    )

    has_manager = ChoiceFilter(
        field_name='manager',
        label=_('Manager'),
        choices=[
            ('', _('All')),
            ('yes', _('Has Manager')),
            ('no', _('No Manager'))
        ],
        empty_label=None,
        lookup='isnull'
    )

    def apply_filters(self, queryset):
        """
        Apply filters to queryset.
        English: Override to handle special 'has_manager' filter logic.
        """
        # English: First apply standard filters from parent
        for name, filter_obj in self.filters.items():
            # Skip has_manager, we'll handle it separately
            if name == 'has_manager':
                continue

            filter_kwargs = filter_obj.get_filter_kwargs()
            if filter_kwargs:
                if '__q' in filter_kwargs:
                    queryset = queryset.filter(filter_kwargs['__q'])
                else:
                    queryset = queryset.filter(**filter_kwargs)

        # English: Handle has_manager special logic
        has_manager_filter = self.filters.get('has_manager')
        if has_manager_filter and has_manager_filter.value:
            if has_manager_filter.value == 'yes':
                queryset = queryset.filter(manager__isnull=False)
            elif has_manager_filter.value == 'no':
                queryset = queryset.filter(manager__isnull=True)

        return queryset