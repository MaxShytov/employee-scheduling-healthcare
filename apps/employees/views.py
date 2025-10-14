"""
Views for employee management.
"""
import json
from django.apps import apps
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db import transaction
from django.db.models import Q, Count
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView

from apps.core.views.base import BaseListView
from apps.core.views.mixins import FilterMixin, BreadcrumbMixin, ProtectedDeleteMixin
from apps.employees.filters import EmployeeFilterSet
from .models import Department, Location, Position, Employee, EmployeeDocument
from .forms import (
    DepartmentForm, LocationForm, LocationSearchForm, PositionForm,
    EmployeeUserForm, EmployeeForm, EmployeeDocumentForm
)
from apps.core.cache import make_key, make_params_hash, get_or_set_stats


# ============================================
# Employee Views
# ============================================


class EmployeeListView(FilterMixin, BreadcrumbMixin, LoginRequiredMixin, PermissionRequiredMixin, BaseListView):
    """Display list of employees with filtering."""
    model = Employee
    template_name = 'employees/employee_list.html'
    context_object_name = 'employees'
    permission_required = 'employees.view_employee'
    filterset_class = EmployeeFilterSet

    def get_breadcrumbs(self):
        return [
            {'name': _('Dashboard'), 'url': reverse('dashboard:home')},
            {'name': _('Employees'), 'url': None},
        ]

    def get_queryset(self):
        """Apply filters and optimize query."""
        # English: FilterMixin.get_queryset() will automatically apply filters from filterset_class
        queryset = super().get_queryset()

        # English: Optimize with select_related
        queryset = queryset.select_related(
            'user',
            'department',
            'position',
            'location'
        )

        # English: Order by user's name
        return queryset.order_by('user__first_name', 'user__last_name')

    def prepare_table_rows(self, employees):
        """
        Prepare table rows data for data_table component.
        English: Separate method for cleaner get_context_data.

        Args:
            employees: QuerySet of Employee objects

        Returns:
            list: Formatted rows for data_table component
        """
        table_rows = []

        for employee in employees:
            table_rows.append({
                'id': employee.pk,
                'cells': [
                    {
                        'type': 'badge',
                        'text': _('Active') if employee.is_active else _('Inactive'),
                        'color': 'success' if employee.is_active else 'secondary',
                        'subtitle': employee.employee_id
                    },
                    {
                        'type': 'avatar',
                        'name': employee.user.get_full_name(),
                        'subtitle': employee.user.email,
                        'avatar_url': employee.user.profile_picture_url,
                    },
                    {
                        'type': 'badge',
                        'text': employee.department.code if employee.department else '—',
                        'color': 'secondary',
                        'label': employee.department.name if employee.department else None,
                        'subtitle': employee.location.name if employee.location else None
                    },
                    {
                        'type': 'badge',
                        'text': employee.position.code if employee.position else '—',
                        'color': 'info',
                        'label': employee.position.title if employee.position else None
                    },
                    {
                        'type': 'badge',
                        'text': employee.get_employment_type_display(),
                        'color': 'primary' if employee.employment_type == 'FT' else 'warning'
                    },
                    {
                        'type': 'currency',
                        'value': float(employee.hourly_rate) if employee.hourly_rate else 0,
                        'currency': 'CHF',
                        'subtitle': f"{float(employee.weekly_hours):.2f} {_('hrs/week')}" if employee.weekly_hours else None
                    },
                    {
                        'type': 'actions',
                        'actions': [
                            {
                                'type': 'link',
                                # ✅ Используем reverse
                                'url': reverse('employees:employee_detail', kwargs={'pk': employee.pk}),
                                'icon': 'visibility',
                                'title': _('View'),
                                'color': 'primary'
                            },
                            {
                                'type': 'link',
                                # ✅ Используем reverse
                                'url': reverse('employees:employee_update', kwargs={'pk': employee.pk}),
                                'icon': 'edit',
                                'title': _('Edit'),
                                'color': 'secondary'
                            }
                        ]
                    }
                ]
            })

        return table_rows

    def _produce_stats(self):
        # English: Heavy aggregates computed once per TTL
        total = Employee.objects.count()
        active = Employee.objects.filter(is_active=True).count()
        inactive = total - active
        dept_count = Department.objects.filter(is_active=True).count()
        return [
            {'title': _('Total Employees'), 'value': total,
             'icon': 'people', 'bg_color': 'primary'},
            {'title': _('Active'),          'value': active,
             'icon': 'check_circle', 'bg_color': 'success'},
            {'title': _('Inactive'),        'value': inactive,
             'icon': 'cancel', 'bg_color': 'danger'},
            {'title': _('Departments'),     'value': dept_count,
             'icon': 'business', 'bg_color': 'info'},
        ]

    def get_statistics(self):
        # если статистика зависит от фильтров
        params_hash = make_params_hash(self.request.GET)
        key = make_key('stats', 'employees', 'employee_list',
                       'global', params_hash)
        return get_or_set_stats(key, self._produce_stats)

    def get_context_data(self, **kwargs):
        """Add statistics and context."""
        context = super().get_context_data(**kwargs)

        # Statistics cards

        context['stats_cards'] = self.get_statistics()

        # Table columns configuration
        context['table_columns'] = [
            {'title': _('ID')},
            {'title': _('Name'), 'width': '27%'},
            {'title': _('Department'), 'width': '15%'},
            {'title': _('Position'), 'width': '15%'},
            {'title': _('Type'), 'width': '10%'},
            {'title': _('Rate'), 'align': 'end'},
            {'title': _('Actions'), 'width': '10%'},
        ]

        # English: Convert employees to table rows format

        context['table_rows'] = self.prepare_table_rows(context['employees'])

        # Empty state configuration
        context['empty_state_config'] = {
            'icon': 'people_outline',
            'title': _('No employees found'),
            'message': _('Start by adding your first employee or adjust your filters'),
            'button_text': _('Add First Employee'),
            'button_url': reverse('employees:employee_create')
        }

        # Add URLs for actions
        context['employees_create_url'] = reverse_lazy(
            'employees:employee_create')

        return context


class EmployeeFormMixin:
    """
    Mixin to handle dual forms (User + Employee) in Create/Update views.
    Provides both form structure and form handling logic.
    """
    model = Employee
    form_class = EmployeeForm
    template_name = 'employees/employee_form.html'
    user_form_class = EmployeeUserForm

    # ========================================
    # Form Structure (sections)
    # ========================================

    def get_form_sections(self, employee_form, user_form, current_image_url=None):
        """Prepare structured form sections data for Employee."""
        return [
            {
                'title': _('Personal Information'),
                'icon': 'person',
                'fields': [
                    {
                        'field': user_form['profile_picture'],
                        'col_class': 'col-12',
                        'is_image': True,
                        'current_image_url': current_image_url
                    },
                    {'field': user_form['first_name'],
                        'col_class': 'col-md-6'},
                    {'field': user_form['last_name'], 'col_class': 'col-md-6'},
                    {'field': user_form['email'], 'col_class': 'col-md-6'},
                    {'field': user_form['phone'], 'col_class': 'col-md-6'},
                    {'field': user_form['date_of_birth'],
                        'col_class': 'col-md-6'},
                    {'field': user_form['country'], 'col_class': 'col-md-6'},
                ]
            },
            {
                'title': _('Employment Information'),
                'icon': 'work',
                'fields': [
                    {
                        'field': employee_form['employee_id'],
                        'col_class': 'col-md-6',
                        'has_toggle': True,
                        'toggle_field': employee_form['is_active'],
                    },
                    {'field': employee_form['department'],
                        'col_class': 'col-md-6'},
                    {'field': employee_form['position'],
                        'col_class': 'col-md-6'},
                    {'field': employee_form['location'],
                        'col_class': 'col-md-6'},
                    {'field': employee_form['employment_type'],
                        'col_class': 'col-md-6'},
                    {'field': employee_form['weekly_hours'],
                        'col_class': 'col-md-6'},
                    {'field': employee_form['hire_date'],
                        'col_class': 'col-md-6'},
                    {'field': employee_form['hourly_rate'],
                        'col_class': 'col-md-6'},
                ]
            },
            {
                'title': _('Emergency Contact'),
                'icon': 'emergency',
                'fields': [
                    {'field': employee_form['emergency_contact_name'],
                        'col_class': 'col-md-6'},
                    {'field': employee_form['emergency_contact_phone'],
                        'col_class': 'col-md-6'},
                    {'field': employee_form['emergency_contact_relationship'],
                        'col_class': 'col-12'},
                ]
            },
            {
                'title': _('Additional Notes'),
                'icon': 'notes',
                'fields': [
                    {'field': employee_form['notes'], 'col_class': 'col-12'},
                ]
            }
        ]

    def get_user_form_instance(self):
        """
        Override in UpdateView to return existing user.
        Returns None in CreateView (new user).
        """
        return None

    def get_user_form(self):
        """Get user form instance with appropriate data."""
        instance = self.get_user_form_instance()

        if self.request.method == 'POST':
            return self.user_form_class(
                self.request.POST,
                self.request.FILES,
                instance=instance
            )
        return self.user_form_class(instance=instance)

    def get_page_metadata(self):
        """
        Override this to customize page title, subtitle, buttons.
        Returns dict with: page_title, page_subtitle, cancel_url, submit_text
        """
        raise NotImplementedError(
            "Subclasses must implement get_page_metadata()")

    def get_current_image_url(self):
        """Get current profile picture URL for update forms."""
        return None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # English: Initialize user form if not in context
        if 'user_form' not in context:
            context['user_form'] = self.get_user_form()

        # English: Get page metadata (title, subtitle, urls)
        metadata = self.get_page_metadata()
        context.update(metadata)

        # English: Prepare forms list and sections
        context['forms'] = [context['user_form'], context['form']]
        context['form_sections'] = self.get_form_sections(
            context['form'],
            context['user_form'],
            current_image_url=self.get_current_image_url()
        )

        return context

    def post(self, request, *args, **kwargs):
        """Handle POST with both forms."""
        # English: For UpdateView, load the object first (has 'pk' in kwargs)
        # For CreateView, object stays None
        if 'pk' in kwargs or 'slug' in kwargs:
            self.object = self.get_object()
        else:
            self.object = None

        form = self.get_form()
        user_form = self.get_user_form()

        if form.is_valid() and user_form.is_valid():
            return self.forms_valid(form, user_form)
        return self.forms_invalid(form, user_form)

    def forms_valid(self, form, user_form):
        """Override this to customize success behavior."""
        raise NotImplementedError("Subclasses must implement forms_valid()")

    def forms_invalid(self, form, user_form):
        """Handle invalid forms."""
        messages.error(self.request, _('Please correct the errors below.'))
        context = self.get_context_data(form=form)
        context['user_form'] = user_form
        return self.render_to_response(context)

    def get_success_url(self):
        """Default success URL - redirect to detail view."""
        # English: For UpdateView, self.object already exists
        # For CreateView, self.object is set in forms_valid()
        if hasattr(self, 'object') and self.object:
            return reverse_lazy('employees:employee_detail', kwargs={'pk': self.object.pk})
        return reverse_lazy('employees:employee_list')


class EmployeeCreateView(EmployeeFormMixin, BreadcrumbMixin, LoginRequiredMixin, CreateView):
    """Create new employee with user account."""

    def get_breadcrumbs(self):
        """Static breadcrumbs for create view."""
        return [
            {'name': _('Dashboard'), 'url': reverse('dashboard:home')},
            {'name': _('Employees'), 'url': reverse(
                'employees:employee_list')},
            {'name': _('Create'), 'url': None},
        ]

    def get_page_metadata(self):
        """Page metadata for create view."""
        return {
            'page_title': _('Add Employee'),
            'page_subtitle': _('Fill in the employee information below'),
            'cancel_url': reverse_lazy('employees:employee_list'),
            'submit_text': _('Create Employee'),
        }

    def forms_valid(self, form, user_form):
        """Create user and employee."""
        try:
            with transaction.atomic():
                # English: Create user account
                user = user_form.save(commit=False)
                user.username = user.email
                user.set_password('Password123!')
                user.save()

                # English: Create employee
                employee = form.save(commit=False)
                employee.user = user
                employee.save()

                messages.success(
                    self.request,
                    _(f'Employee {employee.full_name} created successfully. Default password: Password123!')
                )
                return redirect('employees:employee_detail', pk=employee.pk)
        except Exception as e:
            messages.error(self.request, _(
                f'Error creating employee: {str(e)}'))
            return self.forms_invalid(form, user_form)


class EmployeeUpdateView(EmployeeFormMixin, BreadcrumbMixin, LoginRequiredMixin, UpdateView):
    """Update existing employee."""

    def get_breadcrumbs(self):
        """Dynamic breadcrumbs with employee name."""
        return [
            {'name': _('Dashboard'), 'url': reverse('dashboard:home')},
            {'name': _('Employees'), 'url': reverse(
                'employees:employee_list')},
            {'name': self.object.full_name, 'url': reverse(
                'employees:employee_detail', kwargs={'pk': self.object.pk})},
            {'name': _('Edit'), 'url': None},
        ]

    def get_user_form_instance(self):
        """Return existing user instance for update."""
        return self.object.user

    def get_current_image_url(self):
        """Return current profile picture URL."""
        if self.object.user.profile_picture:
            return self.object.user.profile_picture.url
        return None

    def get_page_metadata(self):
        """Page metadata for update view."""
        return {
            'page_title': _('Edit Employee'),
            'page_subtitle': _('Update employee information'),
            'cancel_url': reverse_lazy('employees:employee_detail', kwargs={'pk': self.object.pk}),
            'submit_text': _('Save Changes'),
        }

    def forms_valid(self, form, user_form):
        """Update user and employee."""
        user_form.save()
        messages.success(self.request, _('Employee updated successfully.'))
        return super().form_valid(form)


class EmployeeDetailView(BreadcrumbMixin, LoginRequiredMixin, DetailView):
    """Display employee details with tabbed interface."""

    model = Employee
    template_name = 'employees/employee_detail.html'
    context_object_name = 'employee'

    def get_breadcrumbs(self):
        """Breadcrumbs for employee detail."""
        return [
            {'name': _('Dashboard'), 'url': reverse('dashboard:home')},
            {'name': _('Employees'), 'url': reverse('employees:employee_list')},
            {'name': self.object.full_name, 'url': None},
        ]

    def get_header_actions(self):
        """
        Prepare header actions for page_header component.
        English: Edit and delete buttons configuration.
        
        Returns:
            list: Action buttons for header
        """
        return [
            {
                'label': _('Edit'),
                'icon': 'edit',
                'href': reverse('employees:employee_update', kwargs={'pk': self.object.pk}),
                'style': 'primary'
            },
            {
                'label': _('Delete'),
                'icon': 'delete',
                'href': reverse('employees:employee_delete', kwargs={'pk': self.object.pk}),
                'style': 'danger'
            }
        ]

    def get_tabs_config(self, documents_count):
        """
        Prepare tabs configuration.
        English: Tab navigation with badge counts.
        
        Args:
            documents_count: Number of documents for badge
            
        Returns:
            list: Tabs configuration
        """
        return [
            {
                'id': 'personal',
                'label': _('Personal Info'),
                'icon': 'person',
                'url': '?tab=personal'
            },
            {
                'id': 'work',
                'label': _('Work Info'),
                'icon': 'work',
                'url': '?tab=work'
            },
            {
                'id': 'documents',
                'label': _('Documents'),
                'icon': 'description',
                'badge': documents_count,
                'url': '?tab=documents'
            }
        ]

    def get_personal_sections(self):
        """
        Prepare personal information sections.
        English: Personal and emergency contact data for detail view.
        
        Returns:
            list: Section data for info display component
        """
        employee = self.object
        
        return [
            {
                'title': _('Personal Information'),
                'icon': 'person',
                'show_divider': False,
                'items': [
                    {'label': _('First Name'), 'value': employee.user.first_name},
                    {'label': _('Last Name'), 'value': employee.user.last_name},
                    {'label': _('Email Address'), 'value': employee.user.email},
                    {'label': _('Phone Number'), 'value': employee.user.phone or '—'},
                    {'label': _('Date of Birth'), 'value': employee.user.date_of_birth or '—'},
                    {
                        'label': _('Country'),
                        'value': employee.user.country.name if employee.user.country else '—'
                    },
                ]
            },
            {
                'title': _('Emergency Contact'),
                'icon': 'emergency',
                'show_divider': True,
                'items': [
                    {
                        'label': _('Contact Name'),
                        'value': employee.emergency_contact_name or '—'
                    },
                    {
                        'label': _('Contact Phone'),
                        'value': employee.emergency_contact_phone or '—'
                    },
                    {
                        'label': _('Relationship'),
                        'value': employee.emergency_contact_relationship or '—',
                        'col_class': 'col-12'
                    },
                ]
            }
        ]

    def get_work_sections(self):
        """
        Prepare work information sections.
        English: Employment details including termination if applicable.
        
        Returns:
            list: Section data for info display component
        """
        employee = self.object
        
        items = [
            {'label': _('Employee ID'), 'value': employee.employee_id},
            {'label': _('Employment Type'), 'value': employee.get_employment_type_display()},
            {
                'label': _('Department'),
                'value': employee.department.name,
                'badge_text': employee.department.code,
                'badge_class': 'bg-secondary'
            },
            {
                'label': _('Position'),
                'value': employee.position.title,
                'badge_text': employee.position.code,
                'badge_class': 'bg-info'
            },
            {
                'label': _('Location'),
                'value': employee.location.name if employee.location else '—',
            },
            {
                'label': _('Hire Date'),
                'value': employee.hire_date.strftime('%B %d, %Y') if employee.hire_date else '—'
            },
            {
                'label': _('Weekly Hours'),
                'value': f"{employee.weekly_hours} hours" if employee.weekly_hours else '—'
            },
            {
                'label': _('Hourly Rate'),
                'value': f"CHF {employee.hourly_rate:.2f}" if employee.hourly_rate else '—'
            },
            {
                'label': _('Years of Service'),
                'value': f"{employee.years_of_service} years" if employee.years_of_service else '—'
            },
        ]
        
        # English: Add termination info if applicable
        if employee.termination_date:
            items.append({
                'label': _('Termination Date'),
                'value': employee.termination_date.strftime('%B %d, %Y')
            })
        
        return [
            {
                'title': _('Employment Information'),
                'icon': 'work',
                'show_divider': False,
                'items': items
            }
        ]

    def prepare_documents_table(self, documents):
        """
        Prepare documents table data.
        English: Convert documents queryset to table rows format.
        
        Args:
            documents: QuerySet of EmployeeDocument objects
            
        Returns:
            dict: Table columns and rows configuration
        """
        if not documents.exists():
            return None
        
        employee = self.object
        
        columns = [
            {'title': _('Title')},
            {'title': _('Type')},
            {'title': _('Uploaded')},
            {'title': _('Actions'), 'align': 'end'},
        ]
        
        rows = []
        for doc in documents:
            rows.append({
                'id': doc.pk,
                'cells': [
                    {'type': 'text', 'value': doc.title},
                    {
                        'type': 'badge',
                        'text': doc.get_document_type_display(),
                        'color': 'info'
                    },
                    {'type': 'text', 'value': doc.created_at.strftime('%Y-%m-%d')},
                    {
                        'type': 'actions',
                        'actions': [
                            {
                                'type': 'link',
                                'url': doc.file.url,
                                'icon': 'download',
                                'color': 'primary',
                                'title': _('Download')
                            },
                            {
                                'type': 'link',
                                'url': reverse(
                                    'employees:document_delete',
                                    kwargs={'pk': employee.pk, 'doc_pk': doc.pk}
                                ),
                                'icon': 'delete',
                                'color': 'danger',
                                'title': _('Delete')
                            }
                        ]
                    }
                ]
            })
        
        return {'columns': columns, 'rows': rows}

    def get_context_data(self, **kwargs):
        """Add tab-specific context data."""
        context = super().get_context_data(**kwargs)
        employee = self.object

        # English: Determine active tab from query params
        active_tab = self.request.GET.get('tab', 'personal')
        context['active_tab'] = active_tab

        # English: Page header data
        context['page_subtitle'] = f"{employee.position.title} • {employee.department.name}"
        context['back_url'] = reverse('employees:employee_list')
        context['header_actions'] = self.get_header_actions()

        # English: Get documents for all tabs (needed for badge count)
        documents = employee.documents.all()

        # English: Tabs configuration
        context['tabs'] = self.get_tabs_config(documents.count())

        # English: Tab-specific sections
        if active_tab == 'personal':
            context['personal_sections'] = self.get_personal_sections()
        elif active_tab == 'work':
            context['work_sections'] = self.get_work_sections()

        # English: Documents tab - ALWAYS prepare this data
        context['documents'] = documents
        context['document_upload_url'] = reverse(
            'employees:document_upload',
            kwargs={'pk': employee.pk}
        )
        context['documents_actions'] = [
            {
                'label': _('Upload Document'),
                'icon': 'upload',
                'href': context['document_upload_url'],
                'style': 'primary'
            }
        ]

        # English: Prepare documents table if there are documents
        documents_table = self.prepare_documents_table(documents)
        if documents_table:
            context['documents_columns'] = documents_table['columns']
            context['documents_rows'] = documents_table['rows']

        return context


class EmployeeDeleteView(BreadcrumbMixin, LoginRequiredMixin, DeleteView):
    """Delete employee with validation and proper error handling."""
    
    model = Employee
    template_name = 'employees/employee_confirm_delete.html'
    success_url = reverse_lazy('employees:employee_list')

    def get_breadcrumbs(self):
        """Breadcrumbs for employee delete."""
        return [
            {'name': _('Dashboard'), 'url': reverse('dashboard:home')},
            {'name': _('Employees'), 'url': reverse('employees:employee_list')},
            {'name': self.object.full_name, 'url': reverse('employees:employee_detail', kwargs={'pk': self.object.pk})},
            {'name': _('Delete'), 'url': None},
        ]


    def get_blocking_references(self):
        """
        Check for blocking references that prevent deletion.
        English: Returns list of blocking references with details.
        Uses app registry to avoid import errors for optional apps.
        
        Returns:
            list: Blocking references or empty list if safe to delete
        """
        employee = self.object
        blocking = []
        
        # English: Check for active shifts (if schedules app exists)
        if apps.is_installed('apps.schedules'):
            try:
                Shift = apps.get_model('schedules', 'Shift')
                from django.utils import timezone
                
                future_shifts = Shift.objects.filter(
                    employee=employee,
                    start_datetime__gte=timezone.now()
                ).count()
                
                if future_shifts > 0:
                    blocking.append({
                        'type': 'future_shifts',
                        'count': future_shifts,
                        'message': _('%(count)d future shift(s) scheduled') % {'count': future_shifts}
                    })
            except LookupError:
                # English: Model doesn't exist yet
                pass
        
        # English: Check for timeclock records (if timeclock app exists)
        if apps.is_installed('apps.timeclock'):
            try:
                TimeEntry = apps.get_model('timeclock', 'TimeEntry')
                
                open_entries = TimeEntry.objects.filter(
                    employee=employee,
                    clock_out__isnull=True
                ).count()
                
                if open_entries > 0:
                    blocking.append({
                        'type': 'open_timeclock',
                        'count': open_entries,
                        'message': _('%(count)d open timeclock entry(ies)') % {'count': open_entries}
                    })
            except LookupError:
                # English: Model doesn't exist yet
                pass
        
        # English: Check for uploaded documents (always available)
        document_count = employee.documents.count()
        if document_count > 0:
            blocking.append({
                'type': 'documents',
                'count': document_count,
                'message': _('%(count)d uploaded document(s)') % {'count': document_count}
            })
        
        return blocking

    def get_warning_items(self):
        """
        Get list of items that will be deleted.
        English: Information about what will be permanently deleted.
        
        Returns:
            list: Warning items for display
        """
        return [
            _('Employee profile and employment history'),
            _('Associated user account'),
            _('All uploaded documents'),
            _('Time clock records (if any)'),
            _('Schedule history'),
        ]

    def get_context_data(self, **kwargs):
        """Add delete confirmation context."""
        context = super().get_context_data(**kwargs)
        employee = self.object
        
        # English: Cancel URL
        context['cancel_url'] = reverse(
            'employees:employee_detail',
            kwargs={'pk': employee.pk}
        )
        
        # English: Main confirmation message
        context['object_name'] = employee.full_name
        context['confirmation_message'] = _('Are you sure you want to delete this employee?')
        context['warning_message'] = _('This action cannot be undone.')
        
        # English: Warning items
        context['warning_items'] = self.get_warning_items()
        
        # English: Check for blocking references
        blocking_refs = self.get_blocking_references()
        context['has_blocking_refs'] = len(blocking_refs) > 0
        context['blocking_refs'] = blocking_refs
        
        # English: If blocked, show appropriate message
        if context['has_blocking_refs']:
            context['blocking_message'] = _(
                'Cannot delete this employee. Please resolve the following issues first:'
            )
        
        return context

    def post(self, request, *args, **kwargs):
        """Handle POST with validation."""
        self.object = self.get_object()
        
        # English: Check for blocking references before deletion
        blocking_refs = self.get_blocking_references()
        
        if blocking_refs:
            # English: Build error message
            messages_list = [ref['message'] for ref in blocking_refs]
            error_msg = _('Cannot delete employee: ') + '; '.join(messages_list)
            messages.error(request, error_msg)
            return redirect('employees:employee_detail', pk=self.object.pk)
        
        # English: Safe to delete - proceed
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        """Handle successful deletion."""
        employee_name = self.object.full_name
        
        # English: Delete user account along with employee
        user = self.object.user
        
        messages.success(
            self.request,
            _('Employee "%(name)s" has been deleted successfully.') % {'name': employee_name}
        )
        
        # English: Delete employee (cascade will handle documents)
        response = super().form_valid(form)
        
        # English: Delete associated user account
        if user:
            user.delete()
        
        return response

# ============================================
# Bulk Actions (временная заглушка)
# ============================================


@require_POST
@login_required
def employee_bulk_action(request):
    """
    Handle bulk actions for employees.
    TODO: Implement actual bulk operations
    """
    try:
        data = json.loads(request.body)
        action = data.get('action')
        ids = data.get('ids', [])

        # Временная логика - просто возвращаем успех
        # TODO: Реализовать действительные операции

        if action == 'export':
            # Будет реализовано позже
            return JsonResponse({'status': 'success', 'message': 'Export functionality coming soon'})

        elif action == 'archive':
            # Будет реализовано позже
            return JsonResponse({'status': 'success', 'message': 'Archive functionality coming soon'})

        elif action == 'delete':
            # Будет реализовано позже
            return JsonResponse({'status': 'success', 'message': 'Bulk delete functionality coming soon'})

        else:
            return JsonResponse({'status': 'error', 'message': 'Unknown action'}, status=400)

    except Exception as e:
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

# ============================================
# Department Views
# ============================================


class DepartmentListView(LoginRequiredMixin, ListView):
    model = Department
    template_name = 'employees/department_list.html'
    context_object_name = 'departments'
    paginate_by = 25

    def get_queryset(self):
        return Department.objects.annotate(
            active_employee_count=Count(
                'employees', filter=Q(employees__is_active=True))
        ).order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Departments'
        context['create_url'] = reverse_lazy('employees:department_create')

        # Breadcrumbs
        context['breadcrumb_items'] = [
            {'name': 'Employees', 'url': reverse('employees:employee_list')},
            {'name': 'Departments'},
        ]

        return context


class DepartmentCreateView(LoginRequiredMixin, CreateView):
    model = Department
    form_class = DepartmentForm
    template_name = 'employees/department_form.html'
    success_url = reverse_lazy('employees:department_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('Add Department')
        context['cancel_url'] = reverse_lazy('employees:department_list')

        # Breadcrumbs
        context['breadcrumb_items'] = [
            {'name': _('Employees'), 'url': reverse(
                'employees:employee_list')},
            {'name': _('Departments'), 'url': reverse(
                'employees:department_list')},
            {'name': _('Create')},
        ]

        return context

    def form_valid(self, form):
        messages.success(self.request, _('Department created successfully.'))
        return super().form_valid(form)


class DepartmentUpdateView(LoginRequiredMixin, UpdateView):
    model = Department
    form_class = DepartmentForm
    template_name = 'employees/department_form.html'
    success_url = reverse_lazy('employees:department_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('Edit Department')
        context['cancel_url'] = reverse_lazy('employees:department_list')

        # Breadcrumbs
        context['breadcrumb_items'] = [
            {'name': _('Employees'), 'url': reverse(
                'employees:employee_list')},
            {'name': _('Departments'), 'url': reverse(
                'employees:department_list')},
            {'name': self.object.name},
        ]

        return context

    def form_valid(self, form):
        messages.success(self.request, _('Department updated successfully.'))
        return super().form_valid(form)


class DepartmentDeleteView(LoginRequiredMixin, DeleteView):
    model = Department
    template_name = 'employees/department_confirm_delete.html'
    success_url = reverse_lazy('employees:department_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        emp_count = self.object.employees.filter(is_active=True).count()
        context['emp_count'] = emp_count
        context['list_url'] = reverse_lazy('employees:department_list')

        # Prepare HTML messages
        context['message_html'] = mark_safe(
            f'{_("Are you sure you want to delete")} <strong>{self.object.name}</strong>?<br>'
            f'{_("This action cannot be undone.")}'
        )

        if emp_count > 0:
            context['blocking_html'] = mark_safe(
                f'{_("This department has")} <strong>{emp_count}</strong> {_("active employee(s).")} '
                f'{_("You cannot delete a department with active employees. Please reassign them first.")}'
            )

        # Breadcrumbs
        context['breadcrumb_items'] = [
            {'name': _('Employees'), 'url': reverse(
                'employees:employee_list')},
            {'name': _('Departments'), 'url': reverse(
                'employees:department_list')},
            {'name': self.object.name, 'url': None},
            {'name': _('Delete')},
        ]

        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        emp_count = self.object.employees.filter(is_active=True).count()

        if emp_count > 0:
            messages.error(
                request,
                _('Cannot delete department with %(count)d active employee(s).') % {
                    'count': emp_count}
            )
            return redirect('employees:department_list')

        messages.success(request, _('Department deleted successfully.'))
        return super().post(request, *args, **kwargs)


# ============================================
# Position Views
# ============================================

class PositionListView(LoginRequiredMixin, ListView):
    model = Position
    template_name = 'employees/position_list.html'
    context_object_name = 'positions'
    paginate_by = 25

    def get_queryset(self):
        return Position.objects.annotate(
            employee_count=Count(
                'employees', filter=Q(employees__is_active=True))
        ).order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('Positions')
        context['create_url'] = reverse_lazy('employees:position_create')

        # Breadcrumbs
        context['breadcrumb_items'] = [
            {'name': _('Employees'), 'url': reverse(
                'employees:employee_list')},
            {'name': _('Positions')},
        ]

        return context


class PositionCreateView(LoginRequiredMixin, CreateView):
    model = Position
    form_class = PositionForm
    template_name = 'employees/position_form.html'
    success_url = reverse_lazy('employees:position_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('Add Position')
        context['cancel_url'] = reverse_lazy('employees:position_list')

        # Breadcrumbs
        context['breadcrumb_items'] = [
            {'name': _('Employees'), 'url': reverse(
                'employees:employee_list')},
            {'name': _('Positions'), 'url': reverse(
                'employees:position_list')},
            {'name': _('Create')},
        ]

        return context

    def form_valid(self, form):
        messages.success(self.request, _('Position created successfully.'))
        return super().form_valid(form)


class PositionUpdateView(LoginRequiredMixin, UpdateView):
    model = Position
    form_class = PositionForm
    template_name = 'employees/position_form.html'
    success_url = reverse_lazy('employees:position_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('Edit Position')
        context['cancel_url'] = reverse_lazy('employees:position_list')

        # Breadcrumbs
        context['breadcrumb_items'] = [
            {'name': _('Employees'), 'url': reverse(
                'employees:employee_list')},
            {'name': _('Positions'), 'url': reverse(
                'employees:position_list')},
            {'name': self.object.name},
        ]

        return context

    def form_valid(self, form):
        messages.success(self.request, _('Position updated successfully.'))
        return super().form_valid(form)


class PositionDeleteView(LoginRequiredMixin, DeleteView):
    model = Position
    template_name = 'employees/position_confirm_delete.html'
    success_url = reverse_lazy('employees:position_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        emp_count = self.object.employees.filter(is_active=True).count()
        context['emp_count'] = emp_count
        context['list_url'] = reverse_lazy('employees:position_list')

        # Prepare HTML messages
        context['message_html'] = mark_safe(
            f'{_("Are you sure you want to delete")} <strong>{self.object.name}</strong>?<br>'
            f'{_("This action cannot be undone.")}'
        )

        if emp_count > 0:
            context['blocking_html'] = mark_safe(
                f'{_("This position has")} <strong>{emp_count}</strong> {_("active employee(s).")} '
                f'{_("You cannot delete a position with active employees. Please reassign them first.")}'
            )

        # Breadcrumbs
        context['breadcrumb_items'] = [
            {'name': _('Employees'), 'url': reverse(
                'employees:employee_list')},
            {'name': _('Positions'), 'url': reverse(
                'employees:position_list')},
            {'name': self.object.name, 'url': None},
            {'name': _('Delete')},
        ]

        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        emp_count = self.object.employees.filter(is_active=True).count()

        if emp_count > 0:
            messages.error(
                request,
                _('Cannot delete position with %(count)d active employee(s).') % {
                    'count': emp_count}
            )
            return redirect('employees:position_list')

        messages.success(request, _('Position deleted successfully.'))
        return super().post(request, *args, **kwargs)

# ============================================
# Document Views
# ============================================


@login_required
def employee_document_upload(request, pk):
    """Upload document for employee."""
    employee = get_object_or_404(Employee, pk=pk)

    if request.method == 'POST':
        form = EmployeeDocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.employee = employee
            document.uploaded_by = request.user
            document.save()

            messages.success(request, _('Document uploaded successfully.'))
            url = reverse('employees:employee_detail', kwargs={
                          'pk': employee.pk}) + '?tab=documents'
            return HttpResponseRedirect(url)
    else:
        form = EmployeeDocumentForm()

    return render(request, 'employees/document_upload.html', {
        'form': form,
        'employee': employee,
        'page_title': _(f'Upload Document for {employee.full_name}')
    })


@login_required
def employee_document_delete(request, pk, doc_pk):
    """Delete employee document."""
    employee = get_object_or_404(Employee, pk=pk)
    
    # English: Try to get document, handle case when already deleted
    try:
        document = EmployeeDocument.objects.get(pk=doc_pk, employee=employee)
    except EmployeeDocument.DoesNotExist:
        # English: Document already deleted (user pressed Back button)
        messages.info(
            request,
            _('This document has already been deleted.')
        )
        url = reverse('employees:employee_detail', kwargs={'pk': employee.pk}) + '?tab=documents'
        return HttpResponseRedirect(url)

    if request.method == 'POST':
        document.delete()
        messages.success(request, _('Document deleted successfully.'))
        url = reverse('employees:employee_detail', kwargs={'pk': employee.pk}) + '?tab=documents'
        return HttpResponseRedirect(url)

    return render(request, 'employees/document_confirm_delete.html', {
        'document': document,
        'employee': employee,
        'page_title': _('Delete Document')
    })


# ============================================
# Location Views (Class-Based)
# ============================================


class LocationListView(LoginRequiredMixin, ListView):
    """List all locations with search and filters."""

    model = Location
    template_name = 'employees/location_list.html'
    context_object_name = 'locations'
    paginate_by = 25

    def get_queryset(self):
        # Use emp_count instead of employee_count to avoid conflict with property
        queryset = Location.objects.annotate(
            emp_count=Count('employees', filter=Q(employees__is_active=True))
        ).all()

        # Get filter parameters
        search = self.request.GET.get('search', '')
        country = self.request.GET.get('country', '')
        is_active = self.request.GET.get('is_active', '')

        # Apply search
        if search:
            queryset = queryset.filter(
                Q(name__icontains=search) |
                Q(city__icontains=search) |
                Q(address__icontains=search)
            )

        # Apply filters
        if country:
            queryset = queryset.filter(country=country)

        if is_active == 'true':
            queryset = queryset.filter(is_active=True)
        elif is_active == 'false':
            queryset = queryset.filter(is_active=False)

        return queryset.order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = LocationSearchForm(self.request.GET)
        context['total_locations'] = Location.objects.filter(
            is_active=True).count()
        context['page_title'] = _('Locations')
        return context


class LocationDetailView(LoginRequiredMixin, DetailView):
    """View location details."""

    model = Location
    template_name = 'employees/location_detail.html'
    context_object_name = 'location'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get employees at this location
        context['employees'] = self.object.employees.filter(
            is_active=True
        ).select_related('user')

        # Get recent shifts at this location (if schedules app exists)
        try:
            from apps.schedules.models import Shift
            context['recent_shifts'] = Shift.objects.filter(
                location=self.object
            ).select_related('employee__user', 'position').order_by('-start_datetime')[:10]
        except ImportError:
            context['recent_shifts'] = None

        context['page_title'] = self.object.name
        return context


class LocationCreateView(LoginRequiredMixin, CreateView):
    """Create new location."""

    model = Location
    form_class = LocationForm
    template_name = 'employees/location_form.html'

    def form_valid(self, form):
        messages.success(
            self.request,
            _('Location "{}" has been created successfully.').format(
                form.instance.name)
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('employees:location_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('Create New Location')
        context['form_action'] = _('Create Location')
        # Breadcrumbs
        context['breadcrumb_items'] = [
            {'name': _('Locations'), 'url': reverse(
                'employees:location_list')},
            {'name': _('Create')},
        ]
        return context


class LocationUpdateView(LoginRequiredMixin, UpdateView):
    """Update existing location."""

    model = Location
    form_class = LocationForm
    template_name = 'employees/location_form.html'

    def form_valid(self, form):
        messages.success(
            self.request,
            _('Location "{}" has been updated successfully.').format(
                form.instance.name)
        )
        return super().form_valid(form)

    def get_success_url(self):
        return reverse('employees:location_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _(f'Edit {self.object.name}')
        context['form_action'] = _('Update Location')

        # Breadcrumbs
        context['breadcrumb_items'] = [
            {'name': _('Locations'), 'url': reverse(
                'employees:location_list')},
            {'name': self.object.name, 'url': self.object.get_absolute_url()},
            {'name': _('Edit')},
        ]
        return context


class LocationDeleteView(LoginRequiredMixin, DeleteView):
    """Delete (deactivate) location."""

    model = Location
    template_name = 'employees/location_confirm_delete.html'
    success_url = reverse_lazy('employees:location_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['employee_count'] = self.object.employee_count
        context['page_title'] = _(f'Delete {self.object.name}')
        # Breadcrumbs
        context['items'] = [
            {'name': 'Home', 'url': '/'},
            {'name': 'Locations', 'url': reverse('employees:location_list')},
            {'name': self.object.name},  # Active item (no URL)
        ]
        return context

    def delete(self, request, *args, **kwargs):
        location = self.get_object()

        # Soft delete - just deactivate
        location.is_active = False
        location.save()

        messages.success(
            request,
            _('Location "{}" has been deactivated.').format(location.name)
        )
        return HttpResponseRedirect(self.success_url)
