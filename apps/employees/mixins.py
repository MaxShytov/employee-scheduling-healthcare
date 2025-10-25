"""
Mixins for employee views.
"""
from django.urls import reverse
from django.utils.translation import gettext_lazy as _


class EmployeeTableMixin:
    """
    Mixin to prepare employee table data with customizable columns.
    English: Provides reusable employee table configuration and row formatting.
    """
    
    # Default columns configuration
    DEFAULT_EMPLOYEE_COLUMNS = [
        'id',
        'name', 
        'department',
        'position',
        'type',
        'rate',
        'actions'
    ]
    
    def get_employee_table_columns(self, exclude=None):
        """
        Get table columns configuration.
        English: Returns list of column definitions, optionally excluding specified columns.
        
        Args:
            exclude: list of column keys to exclude (e.g. ['department', 'id'])
            
        Returns:
            list: Column definitions for data_table component
        """
        exclude = exclude or []
        
        # English: All available columns
        all_columns = {
            'id': {'title': _('ID')},
            'name': {'title': _('Name'), 'width': '35%'},
            'department': {'title': _('Department'), 'width': '15%'},
            'position': {'title': _('Position'), 'width': '15%'},
            'type': {'title': _('Type'), 'width': '10%'},
            'rate': {'title': _('Rate'), 'align': 'end'},
            'actions': {'title': _('Actions'), 'width': '10%'},
        }
        
        # English: Build columns list maintaining order
        columns = []
        for col_key in self.DEFAULT_EMPLOYEE_COLUMNS:
            if col_key not in exclude:
                columns.append(all_columns[col_key])
        
        return columns
    
    def prepare_employee_table_rows(self, employees, exclude_columns=None):
        """
        Prepare employee table rows.
        English: Converts Employee queryset to structured format for data_table component.
        
        Args:
            employees: QuerySet of Employee objects
            exclude_columns: list of column keys to exclude
            
        Returns:
            list: Formatted rows for data_table component
        """
        exclude_columns = exclude_columns or []
        table_rows = []
        
        for employee in employees:
            # English: Build cells dict
            cells_dict = {}
            
            # ID cell
            if 'id' not in exclude_columns:
                cells_dict['id'] = {
                    'type': 'badge',
                    'text': _('Active') if employee.is_active else _('Inactive'),
                    'color': 'success' if employee.is_active else 'secondary',
                    'subtitle': employee.employee_id
                }
            
            # Name cell (always included)
            cells_dict['name'] = {
                'type': 'avatar',
                'name': employee.user.get_full_name(),
                'subtitle': employee.user.email,
                'avatar_url': employee.user.profile_picture_url,
            }
            
            # Department cell
            if 'department' not in exclude_columns:
                cells_dict['department'] = {
                    'type': 'badge',
                    'text': employee.department.code if employee.department else '—',
                    'color': 'secondary',
                    'name': employee.department.name if employee.department else None,
                    'subtitle': employee.location.name if employee.location else None
                }

            # Position cell
            if 'position' not in exclude_columns:
                cells_dict['position'] = {
                    'type': 'badge',
                    'text': employee.position.code if employee.position else '—',
                    'color': 'info',
                    'name': employee.position.title if employee.position else None
                }
            
            # Type cell
            if 'type' not in exclude_columns:
                cells_dict['type'] = {
                    'type': 'badge',
                    'text': employee.get_employment_type_display(),
                    'color': 'primary' if employee.employment_type == 'FT' else 'warning'
                }
            
            # Rate cell
            if 'rate' not in exclude_columns:
                cells_dict['rate'] = {
                    'type': 'currency',
                    'value': float(employee.hourly_rate) if employee.hourly_rate else 0,
                    'currency': 'CHF',
                    'subtitle': f"{float(employee.weekly_hours):.2f} {_('hrs/week')}" if employee.weekly_hours else None
                }
            
            # Actions cell (always included)
            cells_dict['actions'] = {
                'type': 'actions',
                'actions': [
                    {
                        'type': 'link',
                        'url': reverse('employees:employee_detail', kwargs={'pk': employee.pk}),
                        'icon': 'visibility',
                        'title': _('View'),
                        'color': 'primary'
                    },
                    {
                        'type': 'link',
                        'url': reverse('employees:employee_update', kwargs={'pk': employee.pk}),
                        'icon': 'edit',
                        'title': _('Edit'),
                        'color': 'secondary'
                    }
                ]
            }
            
            # English: Build cells list in correct order
            cells = []
            for col_key in self.DEFAULT_EMPLOYEE_COLUMNS:
                if col_key not in exclude_columns and col_key in cells_dict:
                    cells.append(cells_dict[col_key])
            
            table_rows.append({
                'id': employee.pk,
                'cells': cells
            })
        
        return table_rows