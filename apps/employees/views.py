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
from apps.employees.filters import DepartmentFilterSet, EmployeeFilterSet, PositionFilterSet, LocationFilterSet
from apps.employees.mixins import EmployeeTableMixin  # ← Добавьте эту строку
from .models import Department, Location, Position, Employee, EmployeeDocument
from .forms import (
    DepartmentForm, LocationForm, LocationSearchForm, PositionForm,
    EmployeeUserForm, EmployeeForm, EmployeeDocumentForm
)
from apps.core.cache import make_key, make_params_hash, get_or_set_stats


# ============================================
# Employee Views
# ============================================


class EmployeeListView(EmployeeTableMixin, FilterMixin, BreadcrumbMixin, LoginRequiredMixin, PermissionRequiredMixin, BaseListView):
    """Display list of employees with filtering."""
    model = Employee
    template_name = 'employees/employee_list.html'
    context_object_name = 'employees'
    permission_required = 'employees.view_employee'
    filterset_class = EmployeeFilterSet

    def get_breadcrumbs(self):
        return [
            {'label': _('Dashboard'), 'url': reverse('dashboard:home')},
            {'label': _('Employees'), 'url': None},
        ]

    def get_queryset(self):
        """Apply filters and optimize query."""
        queryset = super().get_queryset()
        queryset = queryset.select_related(
            'user',
            'department',
            'position',
            'location'
        )
        return queryset.order_by('user__first_name', 'user__last_name')

    def _produce_stats(self, queryset):
        """
        Compute statistics based on filtered queryset.
        English: Uses the filtered queryset passed as parameter.
        """
        # Calculate stats on filtered queryset
        total = queryset.count()
        active = queryset.filter(is_active=True).count()
        inactive = total - active

        # Department count from filtered employees
        dept_count = queryset.values('department').distinct().count()

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

    def get_statistics(self, queryset):
        """Get statistics with caching based on filtered queryset."""
        params_hash = make_params_hash(self.request.GET)
        key = make_key('stats', 'employees', 'employee_list',
                       'global', params_hash)
        return get_or_set_stats(key, lambda: self._produce_stats(queryset))

    def get_context_data(self, **kwargs):
        """Add statistics and context."""
        # Get full filtered queryset BEFORE pagination for statistics
        full_queryset = self.get_queryset()

        # Now call super() which will paginate the queryset
        context = super().get_context_data(**kwargs)

        # Statistics cards based on full filtered queryset (before pagination)
        context['stats_cards'] = self.get_statistics(full_queryset)

        # English: Use mixin for table configuration
        context['table_columns'] = self.get_employee_table_columns()
        context['table_rows'] = self.prepare_employee_table_rows(context['employees'])

        # Empty state configuration - different for filtered vs unfiltered
        if context.get('has_active_filters'):
            # Filters are active - show "clear filters" message
            context['empty_state_config'] = {
                'icon': 'filter_alt_off',
                'title': _('No employees match your filters'),
                'message': _('Try adjusting or clearing your filters to see more results'),
                'button_text': _('Clear Filters'),
                'button_url': context.get('action_url', reverse('employees:employee_list'))
            }
        else:
            # No filters - show "add first" message
            context['empty_state_config'] = {
                'icon': 'people_outline',
                'title': _('No employees found'),
                'message': _('Start by adding your first employee'),
                'button_text': _('Add First Employee'),
                'button_url': reverse('employees:employee_create')
            }

        context['employees_create_url'] = reverse_lazy('employees:employee_create')

        # English: Page header data
        context['page_title'] = _('Employees')
        context['page_subtitle'] = _('Manage employee records and information')
        context['create_url'] = reverse('employees:employee_create')
        context['back_url'] = reverse('dashboard:home')

        # English: Header actions
        context['header_actions'] = [
            {
                'label': _('Add Employee'),
                'icon': 'add',
                'href': context['create_url'],
                'style': 'primary'
            }
        ]

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
            {'label': _('Dashboard'), 'url': reverse('dashboard:home')},
            {'label': _('Employees'), 'url': reverse(
                'employees:employee_list')},
            {'label': _('Create'), 'url': None},
        ]

    def get_page_metadata(self):
        """Page metadata for create view."""
        return {
            'page_title': _('Add Employee'),
            'page_subtitle': _('Fill in the employee information below'),
            'cancel_url': reverse_lazy('employees:employee_list'),
            'submit_text': _('Create Employee'),
            'show_back': True,
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
            {'label': _('Dashboard'), 'url': reverse('dashboard:home')},
            {'label': _('Employees'), 'url': reverse(
                'employees:employee_list')},
            {'label': self.object.full_name, 'url': reverse(
                'employees:employee_detail', kwargs={'pk': self.object.pk})},
            {'label': _('Edit'), 'url': None},
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
            'show_back': True,
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
            {'label': _('Dashboard'), 'url': reverse('dashboard:home')},
            {'label': _('Employees'), 'url': reverse(
                'employees:employee_list')},
            {'label': self.object.full_name, 'url': None},
        ]

    def get_header_actions(self):
        """
        Prepare header actions for page_header component.
        English: Edit, upload document, and delete buttons configuration.

        Returns:
            list: Action buttons for header
        """
        return [
            {
                'label': _('Upload Document'),
                'icon': 'upload_file',
                'href': reverse('employees:document_upload', kwargs={'pk': self.object.pk}),
                'style': 'primary'
            },
            {
                'label': _('Edit'),
                'icon': 'edit',
                'href': reverse('employees:employee_update', kwargs={'pk': self.object.pk}),
                'style': 'secondary'
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

        Returns:
            list: Tabs configuration for tabs_navigation component
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
                    {'label': _('First Name'), 'value': employee.user.first_name},  # ← 'label' не 'name'
                    {'label': _('Last Name'), 'value': employee.user.last_name},
                    {'label': _('Email Address'), 'value': employee.user.email},
                    {'label': _('Phone Number'), 'value': employee.user.phone or '—'},
                    {'label': _('Date of Birth'), 'value': employee.user.date_of_birth or '—'},
                    {
                        'label': _('Country'),
                        'value': employee.user.country_with_flag or '—'
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
            {'label': _('Employment Type'),
             'value': employee.get_employment_type_display()},
            {
                'name': _('Department'),
                'value': employee.department.name,
                'badge_text': employee.department.code,
                'badge_class': 'bg-secondary'
            },
            {
                'name': _('Position'),
                'value': employee.position.title,
                'badge_text': employee.position.code,
                'badge_class': 'bg-info'
            },
            {
                'name': _('Location'),
                'value': employee.location.name if employee.location else '—',
            },
            {
                'name': _('Hire Date'),
                'value': employee.hire_date.strftime('%B %d, %Y') if employee.hire_date else '—'
            },
            {
                'name': _('Years of Service'),
                'value': f"{employee.years_of_service} years" if employee.years_of_service else '—'
            },            
            {
                'name': _('Weekly Hours'),
                'value': f"{employee.weekly_hours} hours" if employee.weekly_hours else '—'
            },
            {
                'name': _('Hourly Rate'),
                'value': f"CHF {employee.hourly_rate:.2f}" if employee.hourly_rate else '—'
            },

        ]

        # English: Add termination info if applicable
        if employee.termination_date:
            items.append({
                'name': _('Termination Date'),
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
                    {'type': 'text', 'value': doc.created_at.strftime(
                        '%Y-%m-%d')},
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
                                    kwargs={'pk': employee.pk,
                                            'doc_pk': doc.pk}
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
        """Add tab-specific context data using new block system."""
        context = super().get_context_data(**kwargs)
        employee = self.object

        # English: Determine active tab from query params
        active_tab = self.request.GET.get('tab', 'personal')
        context['active_tab'] = active_tab

        # English: Page header data
        context['page_title'] = employee.full_name
        context['page_subtitle'] = f"{employee.position.title} • {employee.department.name}"
        context['back_url'] = reverse('employees:employee_list')
        context['header_actions'] = self.get_header_actions()

        # English: Get documents for all tabs (needed for badge count)
        documents = employee.documents.all()

        # English: Tabs configuration
        context['tabs'] = self.get_tabs_config(documents.count())

        # English: SIDEBAR BLOCKS - Employee profile card
        status_badge = {
            'text': _('Active Employee') if employee.is_active else _('Inactive'),
            'class': 'bg-success' if employee.is_active else 'bg-secondary'
        }

        sidebar_blocks = [
            # Avatar header
            {
                'type': 'avatar_header',
                'avatar_url': employee.user.profile_picture.url if employee.user.profile_picture else None,
                'avatar_initials': employee.user.initials,
                'name': employee.full_name,
                'subtitle': employee.position.title,
                'badge': status_badge
            },
            {'type': 'divider'},
            # Quick info fields
            {
                'type': 'field',
                'icon': 'badge',
                'label': 'ID',
                'value': employee.employee_id
            },
            {
                'type': 'field',
                'icon': 'email',
                'label': 'Email',
                'value': employee.user.email,
                'link': f"mailto:{employee.user.email}"
            },
            {
                'type': 'field',
                'icon': 'phone',
                'label': 'Phone',
                'value': employee.user.phone or '—'
            },
            {
                'type': 'field',
                'icon': 'business',
                'label': 'Dept',
                'value': employee.department.name
            }
        ]

        context['sidebar_blocks'] = sidebar_blocks

        # English: CONTENT BLOCKS - Tab-based content
        content_blocks = []

        # Personal Info tab
        if active_tab == 'personal':
            # Personal Information section
            content_blocks.append({
                'type': 'section_header',
                'icon': 'person',
                'title': _('Personal Information'),
                'tab': 'personal'
            })
            content_blocks.append({
                'type': 'fields_group',
                'tab': 'personal',
                'fields': [
                    {'label': _('Date of Birth'), 'value': employee.user.date_of_birth or '—', 'col_class': 'col-md-6'},
                    {'label': _('Country'), 'value': employee.user.country_with_flag or '—', 'col_class': 'col-md-6'},
                ]
            })

            content_blocks.append({'type': 'divider', 'tab': 'personal'})

            # Emergency Contact section
            content_blocks.append({
                'type': 'section_header',
                'icon': 'emergency',
                'title': _('Emergency Contact'),
                'tab': 'personal'
            })
            content_blocks.append({
                'type': 'fields_group',
                'tab': 'personal',
                'fields': [
                    {'label': _('Contact Name'), 'value': employee.emergency_contact_name or '—', 'col_class': 'col-md-6'},
                    {'label': _('Contact Phone'), 'value': employee.emergency_contact_phone or '—', 'col_class': 'col-md-6'},
                    {'label': _('Relationship'), 'value': employee.emergency_contact_relationship or '—', 'col_class': 'col-12'},
                ]
            })

        # Work Info tab
        elif active_tab == 'work':
            content_blocks.append({
                'type': 'section_header',
                'icon': 'work',
                'title': _('Employment Information'),
                'tab': 'work'
            })

            work_fields = [
                {'label': _('Employment Type'), 'value': employee.get_employment_type_display(), 'col_class': 'col-md-6'},
                {'label': _('Location'), 'value': employee.location.name if employee.location else '—', 'col_class': 'col-md-6'},
                {'label': _('Hire Date'), 'value': employee.hire_date.strftime('%B %d, %Y') if employee.hire_date else '—', 'col_class': 'col-md-6'},
                {'label': _('Years of Service'), 'value': f"{employee.years_of_service} years" if employee.years_of_service else '—', 'col_class': 'col-md-6'},
                {'label': _('Hourly Rate'), 'value': f"CHF {employee.hourly_rate:.2f}" if employee.hourly_rate else '—', 'col_class': 'col-md-6'},
                {'label': _('Weekly Hours'), 'value': f"{employee.weekly_hours} hours" if employee.weekly_hours else '—', 'col_class': 'col-md-6'},
            ]

            if employee.termination_date:
                work_fields.append({
                    'label': _('Termination Date'),
                    'value': employee.termination_date.strftime('%B %d, %Y'),
                    'col_class': 'col-md-6'
                })

            content_blocks.append({
                'type': 'fields_group',
                'tab': 'work',
                'fields': work_fields
            })

        # Documents tab
        elif active_tab == 'documents':
            documents_table = self.prepare_documents_table(documents)
            if documents_table:
                content_blocks.append({
                    'type': 'table',
                    'tab': 'documents',
                    'columns': documents_table['columns'],
                    'rows': documents_table['rows'],
                    'empty_message': _('No documents uploaded')
                })
            else:
                content_blocks.append({
                    'type': 'text_line',
                    'tab': 'documents',
                    'text': _('No documents uploaded yet'),
                    'class': 'text-muted text-center',
                    'margin': 'my-4'
                })

        context['content_blocks'] = content_blocks

        return context


class EmployeeDeleteView(BreadcrumbMixin, LoginRequiredMixin, DeleteView):
    """Delete employee with validation and proper error handling."""

    model = Employee
    template_name = 'employees/employee_confirm_delete.html'
    success_url = reverse_lazy('employees:employee_list')

    def get_breadcrumbs(self):
        """Breadcrumbs for employee delete."""
        return [
            {'label': _('Dashboard'), 'url': reverse('dashboard:home')},
            {'label': _('Employees'), 'url': reverse(
                'employees:employee_list')},
            {'label': self.object.full_name, 'url': reverse(
                'employees:employee_detail', kwargs={'pk': self.object.pk})},
            {'label': _('Delete'), 'url': None},
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
        context['confirmation_message'] = _(
            'Are you sure you want to delete this employee?')
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
            error_msg = _('Cannot delete employee: ') + \
                '; '.join(messages_list)
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
            _('Employee "%(name)s" has been deleted successfully.') % {
                'name': employee_name}
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

class DepartmentListView(FilterMixin, BreadcrumbMixin, LoginRequiredMixin, PermissionRequiredMixin, BaseListView):
    """Display list of departments with filtering and stats."""

    model = Department
    template_name = 'employees/department_list.html'
    context_object_name = 'departments'
    permission_required = 'employees.view_department'
    filterset_class = DepartmentFilterSet

    def get_breadcrumbs(self):
        """Breadcrumbs for department list."""
        return [
            {'label': _('Dashboard'), 'url': reverse('dashboard:home')},
            {'label': _('Employees'), 'url': reverse(
                'employees:employee_list')},
            {'label': _('Departments'), 'url': None},
        ]

    def get_queryset(self):
        """Optimize query with annotations and relations."""
        queryset = super().get_queryset()

        # English: Add employee counts via annotation
        queryset = queryset.annotate(
            total_employees=Count('employees'),
            active_employees=Count(
                'employees', filter=Q(employees__is_active=True)),
            inactive_employees=Count(
                'employees', filter=Q(employees__is_active=False))
        )

        # English: Optimize manager lookup
        queryset = queryset.select_related('manager')

        return queryset.order_by('name')

    def _produce_stats(self, queryset):
        """
        Compute statistics based on filtered queryset.
        English: Uses the filtered queryset passed as parameter.
        """
        # Calculate stats on filtered queryset
        total = queryset.count()
        active = queryset.filter(is_active=True).count()
        inactive = total - active
        with_manager = queryset.filter(manager__isnull=False).count()

        return [
            {
                'title': _('Total Departments'),
                'value': total,
                'icon': 'business',
                'bg_color': 'primary'
            },
            {
                'title': _('Active'),
                'value': active,
                'icon': 'check_circle',
                'bg_color': 'success'
            },
            {
                'title': _('Inactive'),
                'value': inactive,
                'icon': 'cancel',
                'bg_color': 'danger'
            },
            {
                'title': _('With Manager'),
                'value': with_manager,
                'icon': 'person',
                'bg_color': 'info'
            },
        ]

    def get_statistics(self, queryset):
        """Get statistics with caching based on filtered queryset."""
        params_hash = make_params_hash(self.request.GET)
        key = make_key('stats', 'employees', 'department_list',
                       'global', params_hash)
        return get_or_set_stats(key, lambda: self._produce_stats(queryset))

    def prepare_table_rows(self, departments):
        """
        Prepare table rows data for data_table component.
        English: Convert QuerySet to structured dict with cells for templates.
        """
        table_rows = []

        for dept in departments:
            table_rows.append({
                'id': dept.id,
                'cells': [
                    {
                        'type': 'badge',
                        'text': _('Active') if dept.is_active else _('Inactive'),
                        'color': 'success' if dept.is_active else 'secondary',
                        'subtitle': dept.code
                    },
                    {
                        'type': 'strong',
                        'value': dept.name
                    },
                    {
                        'type': 'text',
                        'value': dept.manager_display
                    },
                    {
                        'type': 'text',
                        'value': dept.active_employees,
                        'class': 'text-center'
                    },
                    {
                        'type': 'text',
                        'value': dept.total_employees,
                        'class': 'text-center'
                    },
                    {
                        'type': 'actions',
                        'actions': [
                            {
                                'type': 'link',
                                'url': dept.get_absolute_url(),
                                'icon': 'visibility',
                                'title': _('View'),
                                'color': 'primary'
                            },
                            {
                                'type': 'link',
                                'url': dept.get_edit_url(),
                                'icon': 'edit',
                                'title': _('Edit'),
                                'color': 'secondary'
                            }
                        ]
                    }
                ]
            })

        return table_rows

    def get_context_data(self, **kwargs):
        """Add extra context for template."""
        # Get full filtered queryset BEFORE pagination for statistics
        full_queryset = self.get_queryset()

        # Now call super() which will paginate the queryset
        ctx = super().get_context_data(**kwargs)

        # English: Page header data
        ctx['page_title'] = _('Departments')
        ctx['page_subtitle'] = _('Manage organizational departments')
        ctx['create_url'] = reverse('employees:department_create')
        ctx['back_url'] = reverse('employees:employee_list')

        # English: Header actions
        ctx['header_actions'] = [
            {
                'label': _('Add Department'),
                'icon': 'add',
                'href': ctx['create_url'],
                'style': 'primary'
            }
        ]

        # English: Statistics cards based on full filtered queryset (before pagination)
        ctx['stats_cards'] = self.get_statistics(full_queryset)

        # English: Table configuration
        ctx['table_columns'] = [
            {'title': _('ID'), 'width': '10%'},
            {'title': _('Name'), 'width': '25%'},
            {'title': _('Manager'), 'width': '20%'},
            {'title': _('Active employees'),
             'align': 'center', 'width': '10%'},
            {'title': _('Total employees'), 'align': 'center', 'width': '10%'},
            {'title': _('Actions'), 'width': '15%'},
        ]

        # English: Convert departments to table rows
        ctx['table_rows'] = self.prepare_table_rows(ctx['departments'])

        # English: Empty state configuration - different for filtered vs unfiltered
        if ctx.get('has_active_filters'):
            # Filters are active - show "clear filters" message
            ctx['empty_state_config'] = {
                'icon': 'filter_alt_off',
                'title': _('No departments match your filters'),
                'message': _('Try adjusting or clearing your filters to see more results'),
                'button_text': _('Clear Filters'),
                'button_url': ctx.get('action_url', reverse('employees:department_list'))
            }
        else:
            # No filters - show "add first" message
            ctx['empty_state_config'] = {
                'icon': 'business_center',
                'title': _('No departments found'),
                'message': _('Start by adding your first department'),
                'button_text': _('Add First Department'),
                'button_url': ctx['create_url']
            }

        return ctx


class DepartmentDetailView(EmployeeTableMixin, BreadcrumbMixin, LoginRequiredMixin, PermissionRequiredMixin, DetailView):

    """Display department details with employees listing."""
    
    model = Department
    template_name = 'employees/department_detail.html'
    context_object_name = 'department'
    permission_required = 'employees.view_department'
    
    def get_breadcrumbs(self):
        """Breadcrumbs for department detail."""
        return [
            {'label': _('Dashboard'), 'url': reverse('dashboard:home')},
            {'label': _('Employees'), 'url': reverse('employees:employee_list')},
            {'label': _('Departments'), 'url': reverse('employees:department_list')},
            {'label': self.object.name, 'url': None},
        ]
    
    def get_header_actions(self):
        """Prepare header actions for page_header component."""
        return [
            {
                'label': _('Edit'),
                'icon': 'edit',
                'href': self.object.get_edit_url(),
                'style': 'secondary'
            },
            {
                'label': _('Delete'),
                'icon': 'delete',
                'href': self.object.get_delete_url(),
                'style': 'danger'
            }
        ]
    
    def get_queryset(self):
        """Optimize query."""
        return super().get_queryset().select_related('manager').annotate(
            total_employees=Count('employees'),
            active_employees=Count('employees', filter=Q(employees__is_active=True))
        )
    
    def get_context_data(self, **kwargs):
        """Prepare context for detail view."""
        ctx = super().get_context_data(**kwargs)
        dept = self.object
        
        # English: Page header
        ctx['page_title'] = dept.name
        ctx['page_subtitle'] = _('Department Code: %(code)s') % {'code': dept.code}
        ctx['header_actions'] = self.get_header_actions()
        ctx['back_url'] = reverse('employees:department_list')
        
        # English: Statistics cards
        ctx['stats_cards'] = [
            {
                'title': _('Total Employees'),
                'value': dept.employee_count,
                'icon': 'people',
                'bg_color': 'primary'
            },
            {
                'title': _('Active Employees'),
                'value': dept.active_employee_count,
                'icon': 'check_circle',
                'bg_color': 'success'
            },
            {
                'title': _('Inactive Employees'),
                'value': dept.inactive_employee_count,
                'icon': 'cancel',
                'bg_color': 'secondary'
            },
        ]
        
        # English: Status badge
        status_badge = {
            'text': _('Active') if dept.is_active else _('Inactive'),
            'class': 'bg-success' if dept.is_active else 'bg-secondary'
        }

        # English: Sidebar blocks configuration (new component blocks system)
        sidebar_blocks = [
            # Department name as text (no avatar for departments)
            {
                'type': 'text_line',
                'text': dept.name,
                'class': 'h5 fw-bold text-center',
                'margin': 'mb-1'
            },
            {
                'type': 'text_line',
                'text': f"{_('Code')}: {dept.code}",
                'class': 'text-muted text-center',
                'margin': 'mb-2'
            },
        ]

        # Add badge if present
        if status_badge:
            sidebar_blocks.append({
                'type': 'custom',
                'template': 'core/components/blocks/badge.html',
                'data': {'badge': status_badge, 'align': 'center'}
            })

        sidebar_blocks.extend([
            {'type': 'divider'},
            # Basic Information section
            {
                'type': 'section_header',
                'icon': 'info',
                'title': _('Basic Information')
            },
        ])

        # Add description if present
        if dept.description:
            sidebar_blocks.append({
                'type': 'field',
                'label': _('Description'),
                'value': dept.description
            })

        # Management section
        sidebar_blocks.extend([
            {'type': 'divider'},
            {
                'type': 'section_header',
                'icon': 'person',
                'title': _('Management')
            },
            {
                'type': 'field',
                'icon': 'person',
                'label': _('Manager'),
                'value': dept.manager_display
            },
            {
                'type': 'field',
                'icon': 'phone',
                'label': _('Phone Extension'),
                'value': dept.phone_extension or '—'
            }
        ])

        ctx['sidebar_blocks'] = sidebar_blocks

        # English: Tabs configuration
        ctx['tabs'] = [
            {
                'id': 'employees',
                'label': _('Department Employees'),
                'icon': 'people',
                'url': f"{self.request.path}?tab=employees",
                'active': True
            }
        ]
        ctx['active_tab'] = self.request.GET.get('tab', 'employees')

        # English: Employees list (main content - right column)
        employees = dept.employees.select_related(
            'user', 'position', 'location'
        ).order_by('user__first_name', 'user__last_name')

        # English: Content blocks configuration (new component blocks system)
        content_blocks = [
            {
                'type': 'table',
                'tab': 'employees',  # Belongs to employees tab
                'columns': self.get_employee_table_columns(exclude=['department', 'id']),
                'rows': self.prepare_employee_table_rows(employees, exclude_columns=['department', 'id']),
                'empty_message': _('No employees assigned to this department')
            }
        ]

        # English: Add validity period if present
        if dept.effective_from or dept.effective_to:
            content_blocks.append({
                'type': 'section_header',
                'icon': 'calendar_today',
                'title': _('Validity Period'),
                'tab': 'employees'
            })
            content_blocks.append({
                'type': 'fields_group',
                'tab': 'employees',
                'fields': [
                    {
                        'icon': 'event',
                        'label': _('Effective From'),
                        'value': dept.effective_from.strftime('%B %d, %Y') if dept.effective_from else '—'
                    },
                    {
                        'icon': 'event',
                        'label': _('Effective To'),
                        'value': dept.effective_to.strftime('%B %d, %Y') if dept.effective_to else _('Ongoing')
                    },
                ]
            })

        # English: Add location notes if present
        if dept.location_notes:
            content_blocks.append({'type': 'divider', 'tab': 'employees'})
            content_blocks.append({
                'type': 'section_header',
                'icon': 'location_on',
                'title': _('Additional Details'),
                'tab': 'employees'
            })
            content_blocks.append({
                'type': 'fields_group',
                'tab': 'employees',
                'fields': [
                    {
                        'icon': 'notes',
                        'label': _('Location Notes'),
                        'value': dept.location_notes
                    }
                ]
            })

        ctx['content_blocks'] = content_blocks
        
        return ctx

class DepartmentFormMixin:
    """Shared create/update form behavior for Department views."""
    
    model = Department
    form_class = DepartmentForm
    template_name = 'employees/department_form.html'
    
    def get_page_metadata(self):
        """Return dict: page_title, page_subtitle, cancel_url, submit_text."""
        raise NotImplementedError("Implement get_page_metadata()")
    
    def get_form_sections(self, form):
        """Return list of sections for component-based rendering."""
        return [
            {
                'title': _('Basic Information'),
                'icon': 'info',
                'fields': [
                    {'field': form['name'], 'col_class': 'col-md-6'},
                    {
                        'field': form['code'],
                        'col_class': 'col-md-6',
                        'has_toggle': True,
                        'toggle_field': form['is_active'],
                    },
                    {'field': form['description'], 'col_class': 'col-12'},
                ]
            },
            {
                'title': _('Management & Contact'),
                'icon': 'person',
                'fields': [
                    {'field': form['manager'], 'col_class': 'col-md-6'},
                    {'field': form['phone_extension'], 'col_class': 'col-md-6'},
                    {'field': form['location_notes'], 'col_class': 'col-12'},
                ]
            },
            {
                'title': _('Status & Validity'),
                'icon': 'schedule',
                'fields': [
                    {'field': form['effective_from'], 'col_class': 'col-md-6'},
                    {'field': form['effective_to'], 'col_class': 'col-md-6'},
                ]
            }
        ]
    
    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        meta = self.get_page_metadata()
        ctx.update(meta)
        form = ctx.get('form') or self.get_form()
        ctx['forms'] = [form]
        ctx['form_sections'] = self.get_form_sections(form)
        return ctx
    
    def post(self, request, *args, **kwargs):
        if 'pk' in kwargs:
            self.object = self.get_object()
        else:
            self.object = None
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        return self.form_invalid(form)
    
    def form_valid(self, form):
        """Default save + success message."""
        self.object = form.save()
        messages.success(self.request, _('Department saved successfully.'))
        return super().form_valid(form)
    
    def form_invalid(self, form):
        messages.error(self.request, _('Please correct the errors below.'))
        return self.render_to_response(self.get_context_data(form=form))
    
    def get_success_url(self):
        if getattr(self, 'object', None):
            return reverse('employees:department_detail', kwargs={'pk': self.object.pk})
        return reverse('employees:department_list')


# ============================================
# Department Create / Update Views
# ============================================

class DepartmentCreateView(DepartmentFormMixin, BreadcrumbMixin, LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Create new department."""
    
    permission_required = 'employees.add_department'
    
    def get_breadcrumbs(self):
        """Breadcrumbs for department create."""
        return [
            {'label': _('Dashboard'), 'url': reverse('dashboard:home')},
            {'label': _('Employees'), 'url': reverse('employees:employee_list')},
            {'label': _('Departments'), 'url': reverse('employees:department_list')},
            {'label': _('Create'), 'url': None},
        ]
    
    def get_page_metadata(self):
        """Page metadata for create view."""
        return {
            'page_title': _('Create Department'),
            'page_subtitle': _('Add a new department to the organization'),
            'cancel_url': reverse_lazy('employees:department_list'),
            'submit_text': _('Create Department'),
            'show_back': True,
        }


class DepartmentUpdateView(DepartmentFormMixin, BreadcrumbMixin, LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Update existing department."""
    
    permission_required = 'employees.change_department'
    
    def get_breadcrumbs(self):
        """Breadcrumbs for department update."""
        return [
            {'label': _('Dashboard'), 'url': reverse('dashboard:home')},
            {'label': _('Employees'), 'url': reverse('employees:employee_list')},
            {'label': _('Departments'), 'url': reverse('employees:department_list')},
            {'label': self.object.name, 'url': reverse('employees:department_detail', kwargs={'pk': self.object.pk})},
            {'label': _('Edit'), 'url': None},
        ]
    
    def get_page_metadata(self):
        """Page metadata for update view."""
        return {
            'page_title': _('Edit Department'),
            'page_subtitle': _('Update department information'),
            'cancel_url': reverse_lazy('employees:department_detail', kwargs={'pk': self.object.pk}),
            'submit_text': _('Save Changes'),
            'show_back': True,
        }


# ============================================
# Department Delete View
# ============================================

class DepartmentDeleteView(BreadcrumbMixin, LoginRequiredMixin, PermissionRequiredMixin, ProtectedDeleteMixin, DeleteView):
    """Delete department with validation."""
    
    model = Department
    template_name = 'employees/department_confirm_delete.html'
    success_url = reverse_lazy('employees:department_list')
    permission_required = 'employees.delete_department'
    
    def get_breadcrumbs(self):
        """Breadcrumbs for department delete."""
        return [
            {'label': _('Dashboard'), 'url': reverse('dashboard:home')},
            {'label': _('Employees'), 'url': reverse('employees:employee_list')},
            {'label': _('Departments'), 'url': reverse('employees:department_list')},
            {'label': self.object.name, 'url': reverse('employees:department_detail', kwargs={'pk': self.object.pk})},
            {'label': _('Delete'), 'url': None},
        ]
    
    def get_blocking_references(self):
        """
        Check for blocking references.
        English: Returns list of blocking issues preventing deletion.
        """
        dept = self.object
        blocking = []
        
        # English: Check for active employees
        active_count = dept.employees.filter(is_active=True).count()
        if active_count > 0:
            blocking.append({
                'type': 'active_employees',
                'count': active_count,
                'message': _('%(count)d active employee(s) assigned') % {'count': active_count}
            })
        
        # English: Check for any employees (active or inactive)
        total_count = dept.employees.count()
        if total_count > 0 and active_count == 0:
            blocking.append({
                'type': 'employees_history',
                'count': total_count,
                'message': _('%(count)d employee(s) in history') % {'count': total_count}
            })
        
        return blocking
    
    def get_context_data(self, **kwargs):
        """Add delete confirmation context."""
        ctx = super().get_context_data(**kwargs)
        dept = self.object
        
        # English: Cancel URL
        ctx['cancel_url'] = reverse('employees:department_detail', kwargs={'pk': dept.pk})
        
        # English: Confirmation messages
        ctx['object_name'] = dept.name
        ctx['confirmation_message'] = _('Are you sure you want to delete this department?')
        ctx['warning_message'] = _('This action cannot be undone.')
        
        # English: Check for blocking references
        blocking_refs = self.get_blocking_references()
        ctx['has_blocking_refs'] = len(blocking_refs) > 0
        ctx['blocking_refs'] = blocking_refs
        
        if ctx['has_blocking_refs']:
            ctx['blocking_message'] = _(
                'Cannot delete this department. Please resolve the following issues first:'
            )
        
        return ctx
    
    def post(self, request, *args, **kwargs):
        """Handle POST with validation."""
        self.object = self.get_object()
        
        # English: Check for blocking references
        blocking_refs = self.get_blocking_references()
        
        if blocking_refs:
            messages_list = [ref['message'] for ref in blocking_refs]
            error_msg = _('Cannot delete department: ') + '; '.join(messages_list)
            messages.error(request, error_msg)
            return redirect('employees:department_detail', pk=self.object.pk)
        
        # English: Safe to delete
        return super().post(request, *args, **kwargs)
    
    def form_valid(self, form):
        """Handle successful deletion."""
        dept_name = self.object.name
        messages.success(
            self.request,
            _('Department "%(name)s" has been deleted successfully.') % {'name': dept_name}
        )
        return super().form_valid(form)

# ============================================
# Position Views
# ============================================


class PositionListView(FilterMixin, BreadcrumbMixin, LoginRequiredMixin, PermissionRequiredMixin, BaseListView):
    """Display list of positions with filtering and stats."""

    model = Position
    template_name = 'employees/position_list.html'
    context_object_name = 'positions'
    permission_required = 'employees.view_position'
    filterset_class = PositionFilterSet

    def get_breadcrumbs(self):
        """Breadcrumbs for position list."""
        return [
            {'label': _('Dashboard'), 'url': reverse('dashboard:home')},
            {'label': _('Employees'), 'url': reverse('employees:employee_list')},
            {'label': _('Positions'), 'url': None},
        ]

    def get_queryset(self):
        """Optimize query with annotations."""
        queryset = super().get_queryset()

        # English: Add employee counts via annotation
        queryset = queryset.annotate(
            total_employees=Count('employees'),
            active_employees=Count('employees', filter=Q(employees__is_active=True)),
            inactive_employees=Count('employees', filter=Q(employees__is_active=False))
        )

        return queryset.order_by('title')

    def _produce_stats(self, queryset):
        """
        Compute statistics based on filtered queryset.
        English: Uses the filtered queryset passed as parameter.
        """
        # Calculate stats on filtered queryset
        total = queryset.count()
        active = queryset.filter(is_active=True).count()
        inactive = total - active
        requires_cert = queryset.filter(requires_certification=True).count()

        return [
            {
                'title': _('Total Positions'),
                'value': total,
                'icon': 'work',
                'bg_color': 'primary'
            },
            {
                'title': _('Active'),
                'value': active,
                'icon': 'check_circle',
                'bg_color': 'success'
            },
            {
                'title': _('Inactive'),
                'value': inactive,
                'icon': 'cancel',
                'bg_color': 'danger'
            },
            {
                'title': _('Requires Certification'),
                'value': requires_cert,
                'icon': 'verified',
                'bg_color': 'info'
            },
        ]

    def get_statistics(self, queryset):
        """Get statistics with caching based on filtered queryset."""
        params_hash = make_params_hash(self.request.GET)
        key = make_key('stats', 'employees', 'position_list', 'global', params_hash)
        return get_or_set_stats(key, lambda: self._produce_stats(queryset))

    def prepare_table_rows(self, positions):
        """
        Prepare table rows data for data_table component.
        English: Convert QuerySet to structured dict with cells for templates.
        """
        table_rows = []

        for pos in positions:
            table_rows.append({
                'id': pos.id,
                'cells': [
                    # Status badge with code as subtitle
                    {
                        'type': 'badge',
                        'text': _('Active') if pos.is_active else _('Inactive'),
                        'color': 'success' if pos.is_active else 'secondary',
                        'subtitle': pos.code
                    },
                    # Position title with description
                    {
                        'type': 'text',
                        'value': pos.title,
                        'subtitle': pos.description[:50] + '...' if pos.description and len(pos.description) > 50 else pos.description or '',
                        'class': 'fw-bold'
                    },
                    # Hourly rate range
                    {
                        'type': 'text',
                        'value': pos.rate_range_display
                    },
                    # Certification required badge
                    {
                        'type': 'badge',
                        'text': _('Required') if pos.requires_certification else _('Not Required'),
                        'color': 'warning' if pos.requires_certification else 'secondary'
                    },
                    # Employee count (only active)
                    {
                        'type': 'text',
                        'value': f"{pos.active_employees} employees",
                        'class': 'text-center'
                    },
                    # Actions
                    {
                        'type': 'actions',
                        'actions': [
                            {
                                'type': 'link',
                                'url': pos.get_absolute_url(),
                                'icon': 'visibility',
                                'title': _('View'),
                                'color': 'primary'
                            },
                            {
                                'type': 'link',
                                'url': pos.get_edit_url(),
                                'icon': 'edit',
                                'title': _('Edit'),
                                'color': 'secondary'
                            }
                        ]
                    }
                ]
            })

        return table_rows

    def get_context_data(self, **kwargs):
        """Add extra context for template."""
        # Get full filtered queryset BEFORE pagination for statistics
        full_queryset = self.get_queryset()

        # Now call super() which will paginate the queryset
        ctx = super().get_context_data(**kwargs)

        # English: Page header data
        ctx['page_title'] = _('Positions')
        ctx['page_subtitle'] = _('Manage job positions and roles')
        ctx['create_url'] = reverse('employees:position_create')
        ctx['back_url'] = reverse('employees:employee_list')

        # English: Header actions
        ctx['header_actions'] = [
            {
                'label': _('Add Position'),
                'icon': 'add',
                'href': ctx['create_url'],
                'style': 'primary'
            }
        ]

        # English: Statistics cards based on full filtered queryset (before pagination)
        ctx['stats_cards'] = self.get_statistics(full_queryset)

        # English: Table configuration
        ctx['table_columns'] = [
            {'title': _('Status'), 'width': '10%'},
            {'title': _('Position Title'), 'width': '25%'},
            {'title': _('Hourly Rate Range'), 'width': '15%'},
            {'title': _('Certification Required'), 'width': '15%'},
            {'title': _('Employees'), 'align': 'center', 'width': '10%'},
            {'title': _('Actions'), 'width': '15%'},
        ]

        # English: Convert positions to table rows
        ctx['table_rows'] = self.prepare_table_rows(ctx['positions'])

        # English: Empty state configuration - different for filtered vs unfiltered
        if ctx.get('has_active_filters'):
            # Filters are active - show "clear filters" message
            ctx['empty_state_config'] = {
                'icon': 'filter_alt_off',
                'title': _('No positions match your filters'),
                'message': _('Try adjusting or clearing your filters to see more results'),
                'button_text': _('Clear Filters'),
                'button_url': ctx.get('action_url', reverse('employees:position_list'))
            }
        else:
            # No filters - show "add first" message
            ctx['empty_state_config'] = {
                'icon': 'work_outline',
                'title': _('No positions found'),
                'message': _('Start by adding your first position'),
                'button_text': _('Add First Position'),
                'button_url': ctx['create_url']
            }

        return ctx


class PositionDetailView(EmployeeTableMixin, BreadcrumbMixin, LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Display position details with employees listing."""

    model = Position
    template_name = 'employees/position_detail.html'
    context_object_name = 'position'
    permission_required = 'employees.view_position'

    def get_breadcrumbs(self):
        """Breadcrumbs for position detail."""
        return [
            {'label': _('Dashboard'), 'url': reverse('dashboard:home')},
            {'label': _('Employees'), 'url': reverse('employees:employee_list')},
            {'label': _('Positions'), 'url': reverse('employees:position_list')},
            {'label': self.object.title, 'url': None},
        ]

    def get_header_actions(self):
        """Prepare header actions for page_header component."""
        return [
            {
                'label': _('Edit'),
                'icon': 'edit',
                'href': self.object.get_edit_url(),
                'style': 'secondary'
            },
            {
                'label': _('Delete'),
                'icon': 'delete',
                'href': self.object.get_delete_url(),
                'style': 'danger'
            }
        ]

    def get_queryset(self):
        """Optimize query."""
        return super().get_queryset().annotate(
            total_employees=Count('employees'),
            active_employees=Count('employees', filter=Q(employees__is_active=True))
        )

    def get_context_data(self, **kwargs):
        """Prepare context for detail view."""
        ctx = super().get_context_data(**kwargs)
        pos = self.object

        # English: Page header
        ctx['page_title'] = pos.title
        ctx['page_subtitle'] = _('Position Code: %(code)s') % {'code': pos.code}
        ctx['header_actions'] = self.get_header_actions()
        ctx['back_url'] = reverse('employees:position_list')

        # English: Statistics cards
        ctx['stats_cards'] = [
            {
                'title': _('Total Employees'),
                'value': pos.employee_count,
                'icon': 'people',
                'bg_color': 'primary'
            },
            {
                'title': _('Active Employees'),
                'value': pos.active_employee_count,
                'icon': 'check_circle',
                'bg_color': 'success'
            },
            {
                'title': _('Inactive Employees'),
                'value': pos.inactive_employee_count,
                'icon': 'cancel',
                'bg_color': 'secondary'
            },
        ]

        # English: Status badge
        status_badge = {
            'text': _('Active') if pos.is_active else _('Inactive'),
            'class': 'bg-success' if pos.is_active else 'bg-secondary'
        }

        # English: Sidebar blocks configuration (new component blocks system)
        sidebar_blocks = [
            # Position title as text (no avatar for positions)
            {
                'type': 'text_line',
                'text': pos.title,
                'class': 'h5 fw-bold text-center',
                'margin': 'mb-1'
            },
            {
                'type': 'text_line',
                'text': f"{_('Code')}: {pos.code}",
                'class': 'text-muted text-center',
                'margin': 'mb-2'
            },
        ]

        # Add badge if present
        if status_badge:
            sidebar_blocks.append({
                'type': 'custom',
                'template': 'core/components/blocks/badge.html',
                'data': {'badge': status_badge, 'align': 'center'}
            })

        sidebar_blocks.extend([
            {'type': 'divider'},
            # Basic Information section
            {
                'type': 'section_header',
                'icon': 'info',
                'title': _('Basic Information')
            },
        ])

        # Add description if present
        if pos.description:
            sidebar_blocks.append({
                'type': 'field',
                'label': _('Description'),
                'value': pos.description
            })

        # Compensation section
        sidebar_blocks.extend([
            {'type': 'divider'},
            {
                'type': 'section_header',
                'icon': 'payments',
                'title': _('Compensation')
            },
            {
                'type': 'field',
                'icon': 'attach_money',
                'label': _('Rate Range'),
                'value': pos.rate_range_display
            },
            {
                'type': 'field',
                'icon': 'trending_up',
                'label': _('Min Rate'),
                'value': f"CHF {pos.min_hourly_rate:.2f}/hr"
            },
            {
                'type': 'field',
                'icon': 'trending_down',
                'label': _('Max Rate'),
                'value': f"CHF {pos.max_hourly_rate:.2f}/hr"
            }
        ])

        # Requirements section
        sidebar_blocks.extend([
            {'type': 'divider'},
            {
                'type': 'section_header',
                'icon': 'verified',
                'title': _('Requirements')
            },
            {
                'type': 'field',
                'icon': 'verified_user',
                'label': _('Certification Required'),
                'value': _('Yes') if pos.requires_certification else _('No')
            }
        ])

        ctx['sidebar_blocks'] = sidebar_blocks

        # English: Tabs configuration
        ctx['tabs'] = [
            {
                'id': 'employees',
                'label': _('Employees in this Position'),
                'icon': 'people',
                'url': f"{self.request.path}?tab=employees",
                'active': True
            }
        ]
        ctx['active_tab'] = self.request.GET.get('tab', 'employees')

        # English: Employees list (main content - right column)
        employees = pos.employees.select_related(
            'user', 'department', 'location'
        ).order_by('user__first_name', 'user__last_name')

        # English: Content blocks configuration (new component blocks system)
        ctx['content_blocks'] = [
            {
                'type': 'table',
                'tab': 'employees',  # Belongs to employees tab
                'columns': self.get_employee_table_columns(exclude=['position', 'id']),
                'rows': self.prepare_employee_table_rows(employees, exclude_columns=['position', 'id']),
                'empty_message': _('No employees assigned to this position')
            }
        ]

        return ctx


class PositionFormMixin:
    """Shared create/update form behavior for Position views."""

    model = Position
    form_class = PositionForm
    template_name = 'employees/position_form.html'

    def get_page_metadata(self):
        """Return dict: page_title, page_subtitle, cancel_url, submit_text."""
        raise NotImplementedError("Implement get_page_metadata()")

    def get_form_sections(self, form):
        """Return list of sections for component-based rendering."""
        return [
            {
                'title': _('Basic Information'),
                'icon': 'info',
                'fields': [
                    {'field': form['title'], 'col_class': 'col-md-6'},
                    {
                        'field': form['code'],
                        'col_class': 'col-md-6',
                        'has_toggle': True,
                        'toggle_field': form['is_active'],
                    },
                    {'field': form['description'], 'col_class': 'col-12'},
                ]
            },
            {
                'title': _('Requirements'),
                'icon': 'verified',
                'fields': [
                    {'field': form['requires_certification'], 'col_class': 'col-md-12'},
                ]
            },
            {
                'title': _('Compensation Range'),
                'icon': 'payments',
                'fields': [
                    {'field': form['min_hourly_rate'], 'col_class': 'col-md-6'},
                    {'field': form['max_hourly_rate'], 'col_class': 'col-md-6'},
                ]
            }
        ]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        meta = self.get_page_metadata()
        ctx.update(meta)
        form = ctx.get('form') or self.get_form()
        ctx['forms'] = [form]
        ctx['form_sections'] = self.get_form_sections(form)
        return ctx

    def post(self, request, *args, **kwargs):
        if 'pk' in kwargs:
            self.object = self.get_object()
        else:
            self.object = None
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        return self.form_invalid(form)

    def form_valid(self, form):
        """Default save + success message."""
        self.object = form.save()
        messages.success(self.request, _('Position saved successfully.'))
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, _('Please correct the errors below.'))
        return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        if getattr(self, 'object', None):
            return reverse('employees:position_detail', kwargs={'pk': self.object.pk})
        return reverse('employees:position_list')


# ============================================
# Position Create / Update Views
# ============================================

class PositionCreateView(PositionFormMixin, BreadcrumbMixin, LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Create new position."""

    permission_required = 'employees.add_position'

    def get_breadcrumbs(self):
        """Breadcrumbs for position create."""
        return [
            {'label': _('Dashboard'), 'url': reverse('dashboard:home')},
            {'label': _('Employees'), 'url': reverse('employees:employee_list')},
            {'label': _('Positions'), 'url': reverse('employees:position_list')},
            {'label': _('Create'), 'url': None},
        ]

    def get_page_metadata(self):
        """Page metadata for create view."""
        return {
            'page_title': _('Create Position'),
            'page_subtitle': _('Add a new position to the organization'),
            'cancel_url': reverse_lazy('employees:position_list'),
            'submit_text': _('Create Position'),
            'show_back': True,
        }


class PositionUpdateView(PositionFormMixin, BreadcrumbMixin, LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Update existing position."""

    permission_required = 'employees.change_position'

    def get_breadcrumbs(self):
        """Breadcrumbs for position update."""
        return [
            {'label': _('Dashboard'), 'url': reverse('dashboard:home')},
            {'label': _('Employees'), 'url': reverse('employees:employee_list')},
            {'label': _('Positions'), 'url': reverse('employees:position_list')},
            {'label': self.object.title, 'url': reverse('employees:position_detail', kwargs={'pk': self.object.pk})},
            {'label': _('Edit'), 'url': None},
        ]

    def get_page_metadata(self):
        """Page metadata for update view."""
        return {
            'page_title': _('Edit Position'),
            'page_subtitle': _('Update position information'),
            'cancel_url': reverse_lazy('employees:position_detail', kwargs={'pk': self.object.pk}),
            'submit_text': _('Save Changes'),
            'show_back': True,
        }


# ============================================
# Position Delete View
# ============================================

class PositionDeleteView(BreadcrumbMixin, LoginRequiredMixin, PermissionRequiredMixin, ProtectedDeleteMixin, DeleteView):
    """Delete position with validation."""

    model = Position
    template_name = 'employees/position_confirm_delete.html'
    success_url = reverse_lazy('employees:position_list')
    permission_required = 'employees.delete_position'

    def get_breadcrumbs(self):
        """Breadcrumbs for position delete."""
        return [
            {'label': _('Dashboard'), 'url': reverse('dashboard:home')},
            {'label': _('Employees'), 'url': reverse('employees:employee_list')},
            {'label': _('Positions'), 'url': reverse('employees:position_list')},
            {'label': self.object.title, 'url': reverse('employees:position_detail', kwargs={'pk': self.object.pk})},
            {'label': _('Delete'), 'url': None},
        ]

    def get_blocking_references(self):
        """
        Check for blocking references.
        English: Returns list of blocking issues preventing deletion.
        """
        pos = self.object
        blocking = []

        # English: Check for active employees
        active_count = pos.employees.filter(is_active=True).count()
        if active_count > 0:
            blocking.append({
                'type': 'active_employees',
                'count': active_count,
                'message': _('%(count)d active employee(s) assigned') % {'count': active_count}
            })

        # English: Check for any employees (active or inactive)
        total_count = pos.employees.count()
        if total_count > 0 and active_count == 0:
            blocking.append({
                'type': 'employees_history',
                'count': total_count,
                'message': _('%(count)d employee(s) in history') % {'count': total_count}
            })

        return blocking

    def get_context_data(self, **kwargs):
        """Add delete confirmation context."""
        ctx = super().get_context_data(**kwargs)
        pos = self.object

        # English: Cancel URL
        ctx['cancel_url'] = reverse('employees:position_detail', kwargs={'pk': pos.pk})

        # English: Confirmation messages
        ctx['object_name'] = pos.title
        ctx['confirmation_message'] = _('Are you sure you want to delete this position?')
        ctx['warning_message'] = _('This action cannot be undone.')

        # English: Check for blocking references
        blocking_refs = self.get_blocking_references()
        ctx['has_blocking_refs'] = len(blocking_refs) > 0
        ctx['blocking_refs'] = blocking_refs

        if ctx['has_blocking_refs']:
            ctx['blocking_message'] = _(
                'Cannot delete this position. Please resolve the following issues first:'
            )

        return ctx

    def post(self, request, *args, **kwargs):
        """Handle POST with validation."""
        self.object = self.get_object()

        # English: Check for blocking references
        blocking_refs = self.get_blocking_references()

        if blocking_refs:
            messages_list = [ref['message'] for ref in blocking_refs]
            error_msg = _('Cannot delete position: ') + '; '.join(messages_list)
            messages.error(request, error_msg)
            return redirect('employees:position_detail', pk=self.object.pk)

        # English: Safe to delete
        return super().post(request, *args, **kwargs)

    def form_valid(self, form):
        """Handle successful deletion."""
        pos_title = self.object.title
        messages.success(
            self.request,
            _('Position "%(title)s" has been deleted successfully.') % {'title': pos_title}
        )
        return super().form_valid(form)

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
        url = reverse('employees:employee_detail', kwargs={
                      'pk': employee.pk}) + '?tab=documents'
        return HttpResponseRedirect(url)

    if request.method == 'POST':
        document.delete()
        messages.success(request, _('Document deleted successfully.'))
        url = reverse('employees:employee_detail', kwargs={
                      'pk': employee.pk}) + '?tab=documents'
        return HttpResponseRedirect(url)

    return render(request, 'employees/document_confirm_delete.html', {
        'document': document,
        'employee': employee,
        'page_title': _('Delete Document')
    })


# ============================================
# Location Views (Class-Based)
# ============================================


class LocationListView(FilterMixin, BreadcrumbMixin, LoginRequiredMixin, PermissionRequiredMixin, BaseListView):
    """Display list of locations with filtering and stats."""

    model = Location
    template_name = 'employees/location_list.html'
    context_object_name = 'locations'
    permission_required = 'employees.view_location'
    filterset_class = LocationFilterSet

    def get_breadcrumbs(self):
        """Breadcrumbs for location list."""
        return [
            {'label': _('Dashboard'), 'url': reverse('dashboard:home')},
            {'label': _('Employees'), 'url': reverse('employees:employee_list')},
            {'label': _('Locations'), 'url': None},
        ]

    def get_queryset(self):
        """Optimize query with annotations and relations."""
        queryset = super().get_queryset()

        # English: Add employee counts via annotation
        queryset = queryset.annotate(
            total_employees=Count('employees'),
            active_employees=Count('employees', filter=Q(employees__is_active=True)),
            inactive_employees=Count('employees', filter=Q(employees__is_active=False))
        )

        # English: Optimize manager lookup
        queryset = queryset.select_related('manager')

        return queryset.order_by('name')

    def _produce_stats(self, queryset):
        """
        Compute statistics based on filtered queryset.
        English: Uses the filtered queryset passed as parameter.
        """
        # Calculate stats on filtered queryset
        total = queryset.count()
        active = queryset.filter(is_active=True).count()
        inactive = total - active
        with_manager = queryset.filter(manager__isnull=False).count()

        return [
            {
                'title': _('Total Locations'),
                'value': total,
                'icon': 'location_on',
                'bg_color': 'primary'
            },
            {
                'title': _('Active'),
                'value': active,
                'icon': 'check_circle',
                'bg_color': 'success'
            },
            {
                'title': _('Inactive'),
                'value': inactive,
                'icon': 'cancel',
                'bg_color': 'danger'
            },
            {
                'title': _('With Manager'),
                'value': with_manager,
                'icon': 'person',
                'bg_color': 'info'
            },
        ]

    def get_statistics(self, queryset):
        """Get statistics with caching based on filtered queryset."""
        params_hash = make_params_hash(self.request.GET)
        key = make_key('stats', 'employees', 'location_list', 'global', params_hash)
        return get_or_set_stats(key, lambda: self._produce_stats(queryset))

    def prepare_table_rows(self, locations):
        """
        Prepare table rows data for data_table component.
        English: Convert QuerySet to structured dict with cells for templates.
        """
        table_rows = []

        for loc in locations:
            manager_display = loc.manager.get_full_name() if loc.manager else '—'

            # Build address for badge name: address, address_line_2, postal_code
            address_parts = []
            if loc.address:
                address_parts.append(loc.address)
            if loc.address_line_2:
                address_parts.append(loc.address_line_2)
            if loc.postal_code:
                address_parts.append(loc.postal_code)

            address_display = ", ".join(address_parts) if address_parts else "—"

            # Build subtitle: state, country
            subtitle_parts = []
            if loc.state_province:
                subtitle_parts.append(loc.state_province)
            if loc.country:
                subtitle_parts.append(loc.get_country_display())

            address_subtitle = ", ".join(subtitle_parts) if subtitle_parts else ""

            table_rows.append({
                'id': loc.id,
                'cells': [
                    {
                        'type': 'badge',
                        'text': _('Active') if loc.is_active else _('Inactive'),
                        'color': 'success' if loc.is_active else 'secondary',
                        'subtitle': loc.code
                    },
                    {
                        'type': 'text',
                        'value': loc.name,
                        'subtitle': loc.city,
                        'class': 'fw-bold'
                    },
                    {
                        'type': 'icon',
                        'icon': loc.country_flag or '🌍',
                        'name': address_display,
                        'subtitle': address_subtitle
                    },
                    {
                        'type': 'text',
                        'value': manager_display
                    },
                    {
                        'type': 'text',
                        'value': loc.active_employees,
                        'class': 'text-center'
                    },
                    {
                        'type': 'text',
                        'value': loc.total_employees,
                        'class': 'text-center'
                    },
                    {
                        'type': 'actions',
                        'actions': [
                            {
                                'type': 'link',
                                'url': loc.get_absolute_url(),
                                'icon': 'visibility',
                                'title': _('View'),
                                'color': 'primary'
                            },
                            {
                                'type': 'link',
                                'url': loc.get_edit_url(),
                                'icon': 'edit',
                                'title': _('Edit'),
                                'color': 'secondary'
                            }
                        ]
                    }
                ]
            })

        return table_rows

    def get_context_data(self, **kwargs):
        """Add extra context for template."""
        # Get full filtered queryset BEFORE pagination for statistics
        full_queryset = self.get_queryset()

        # Now call super() which will paginate the queryset
        ctx = super().get_context_data(**kwargs)

        # English: Page header data
        ctx['page_title'] = _('Locations')
        ctx['page_subtitle'] = _('Manage clinic and office locations')
        ctx['create_url'] = reverse('employees:location_create')
        ctx['back_url'] = reverse('employees:employee_list')

        # English: Header actions
        ctx['header_actions'] = [
            {
                'label': _('Add Location'),
                'icon': 'add',
                'href': ctx['create_url'],
                'style': 'primary'
            }
        ]

        # English: Statistics cards based on full filtered queryset (before pagination)
        ctx['stats_cards'] = self.get_statistics(full_queryset)

        # English: Table configuration
        ctx['table_columns'] = [
            {'title': _('Status'), 'width': '10%'},
            {'title': _('Name'), 'width': '20%'},
            {'title': _('Address'), 'width': '25%'},
            {'title': _('Manager'), 'width': '15%'},
            {'title': _('Active employees'), 'align': 'center', 'width': '10%'},
            {'title': _('Total employees'), 'align': 'center', 'width': '10%'},
            {'title': _('Actions'), 'width': '10%'}
        ]
        ctx['table_rows'] = self.prepare_table_rows(ctx['locations'])

        # English: Empty state config
        if ctx.get('has_active_filters'):
            ctx['empty_state_config'] = {
                'icon': 'filter_alt_off',
                'title': _('No locations match your filters'),
                'message': _('Try adjusting or clearing your filters to see more results'),
                'button_text': _('Clear Filters'),
                'button_url': ctx.get('action_url', reverse('employees:location_list'))
            }
        else:
            ctx['empty_state_config'] = {
                'icon': 'location_on',
                'title': _('No locations found'),
                'message': _('Start by adding your first clinic location'),
                'button_text': _('Add First Location'),
                'button_url': reverse('employees:location_create')
            }

        return ctx


class LocationDetailView(EmployeeTableMixin, BreadcrumbMixin, LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Display location details with employees listing."""

    model = Location
    template_name = 'employees/location_detail.html'
    context_object_name = 'location'
    permission_required = 'employees.view_location'

    def get_breadcrumbs(self):
        """Breadcrumbs for location detail."""
        return [
            {'label': _('Dashboard'), 'url': reverse('dashboard:home')},
            {'label': _('Employees'), 'url': reverse('employees:employee_list')},
            {'label': _('Locations'), 'url': reverse('employees:location_list')},
            {'label': self.object.name, 'url': None},
        ]

    def get_header_actions(self):
        """Prepare header actions for page_header component."""
        return [
            {
                'label': _('Edit'),
                'icon': 'edit',
                'href': self.object.get_edit_url(),
                'style': 'secondary'
            },
            {
                'label': _('Delete'),
                'icon': 'delete',
                'href': self.object.get_delete_url(),
                'style': 'danger'
            }
        ]

    def get_queryset(self):
        """Optimize query."""
        return super().get_queryset().select_related('manager').annotate(
            total_employees=Count('employees'),
            active_employees=Count('employees', filter=Q(employees__is_active=True))
        )

    def get_context_data(self, **kwargs):
        """Prepare context for detail view."""
        ctx = super().get_context_data(**kwargs)
        loc = self.object

        # English: Page header
        ctx['page_title'] = loc.name
        ctx['page_subtitle'] = _('Location Code: %(code)s') % {'code': loc.code}
        ctx['header_actions'] = self.get_header_actions()
        ctx['back_url'] = reverse('employees:location_list')

        # English: Statistics cards
        ctx['stats_cards'] = [
            {
                'title': _('Total Employees'),
                'value': loc.employee_count,
                'icon': 'people',
                'bg_color': 'primary'
            },
            {
                'title': _('Active Employees'),
                'value': loc.active_employee_count,
                'icon': 'check_circle',
                'bg_color': 'success'
            },
            {
                'title': _('Inactive Employees'),
                'value': loc.inactive_employee_count,
                'icon': 'cancel',
                'bg_color': 'secondary'
            },
        ]

        # English: Status badge
        status_badge = {
            'text': _('Active') if loc.is_active else _('Inactive'),
            'class': 'bg-success' if loc.is_active else 'bg-secondary'
        }

        # English: Sidebar blocks configuration (new component blocks system)
        sidebar_blocks = [
            # Location name as text
            {
                'type': 'text_line',
                'text': loc.name,
                'class': 'h5 fw-bold text-center',
                'margin': 'mb-1'
            },
            {
                'type': 'text_line',
                'text': f"{_('Code')}: {loc.code}",
                'class': 'text-muted text-center',
                'margin': 'mb-2'
            },
        ]

        # Add badge if present
        if status_badge:
            sidebar_blocks.append({
                'type': 'custom',
                'template': 'core/components/blocks/badge.html',
                'data': {'badge': status_badge, 'align': 'center'}
            })

        sidebar_blocks.extend([
            {'type': 'divider'},
            # Location section
            {
                'type': 'section_header',
                'icon': 'location_on',
                'title': _('Location')
            },
        ])

        # Build full address in one line: Street, City PostalCode, StateProvince, CountryCode
        address_parts = []

        # Add street address (line 1 and line 2 if present)
        if loc.address:
            street = loc.address
            if loc.address_line_2:
                street = f"{street}, {loc.address_line_2}"
            address_parts.append(street)

        # Add city with postal code
        if loc.city:
            city_part = f"{loc.city} {loc.postal_code}" if loc.postal_code else loc.city
            address_parts.append(city_part)

        # Add state/province if present
        if loc.state_province:
            address_parts.append(loc.state_province)

        # Add country code only (no flag in address line)
        if loc.country:
            address_parts.append(loc.country)

        if address_parts:
            full_address = ", ".join(address_parts)
            sidebar_blocks.append({
                'type': 'field',
                'icon': 'place',
                'label': _('Address'),
                'value': full_address
            })

        # Add geolocation if present
        if loc.latitude and loc.longitude:
            geo_url = f"https://www.google.com/maps?q={loc.latitude},{loc.longitude}"
            sidebar_blocks.append({
                'type': 'field',
                'icon': 'map',
                'label': _('Geo'),
                'value': f"{loc.latitude}, {loc.longitude}",
                'link': geo_url
            })

        # Contact section
        sidebar_blocks.extend([
            {'type': 'divider'},
            {
                'type': 'section_header',
                'icon': 'contact_phone',
                'title': _('Contact')
            },
        ])

        if loc.phone:
            sidebar_blocks.append({
                'type': 'field',
                'icon': 'phone',
                'label': _('Phone'),
                'value': loc.phone
            })

        if loc.email:
            sidebar_blocks.append({
                'type': 'field',
                'icon': 'email',
                'label': _('Email'),
                'value': loc.email
            })

        # Management section
        sidebar_blocks.extend([
            {'type': 'divider'},
            {
                'type': 'section_header',
                'icon': 'person',
                'title': _('Management')
            },
            {
                'type': 'field',
                'icon': 'person',
                'label': _('Manager'),
                'value': loc.manager.get_full_name() if loc.manager else '—'
            },
            {
                'type': 'field',
                'icon': 'account_balance_wallet',
                'label': _('Labor Budget'),
                'value': f"CHF {loc.labor_budget:,.2f}" if loc.labor_budget else '—'
            }
        ])

        # English: Add notes if present
        if loc.notes:
            sidebar_blocks.extend([
                {'type': 'divider'},
                {
                    'type': 'section_header',
                    'icon': 'notes',
                    'title': _('Additional Notes')
                },
                {
                    'type': 'field',
                    'icon': 'notes',
                    'label': _('Notes'),
                    'value': loc.notes
                }
            ])

        ctx['sidebar_blocks'] = sidebar_blocks

        # English: Tabs configuration
        ctx['tabs'] = [
            {
                'id': 'employees',
                'label': _('Location Employees'),
                'icon': 'people',
                'url': f"{self.request.path}?tab=employees",
                'active': True
            }
        ]
        ctx['active_tab'] = self.request.GET.get('tab', 'employees')

        # English: Employees list (main content - right column)
        employees = loc.employees.select_related(
            'user', 'position', 'department'
        ).order_by('user__first_name', 'user__last_name')

        # English: Content blocks configuration (new component blocks system)
        content_blocks = [
            {
                'type': 'table',
                'tab': 'employees',  # Belongs to employees tab
                'columns': self.get_employee_table_columns(exclude=['location', 'id']),
                'rows': self.prepare_employee_table_rows(employees, exclude_columns=['location', 'id']),
                'empty_message': _('No employees assigned to this location')
            }
        ]

        ctx['content_blocks'] = content_blocks

        return ctx


class LocationFormMixin:
    """Shared create/update form behavior for Location views."""

    model = Location
    form_class = LocationForm
    template_name = 'employees/location_form.html'

    def get_page_metadata(self):
        """Return dict: page_title, page_subtitle, cancel_url, submit_text."""
        raise NotImplementedError("Implement get_page_metadata()")

    def get_form_sections(self, form):
        """Return list of sections for component-based rendering."""
        return [
            {
                'title': _('Basic Information'),
                'icon': 'info',
                'fields': [
                    {'field': form['name'], 'col_class': 'col-md-6'},
                    {
                        'field': form['code'],
                        'col_class': 'col-md-6',
                        'has_toggle': True,
                        'toggle_field': form['is_active'],
                    },
                ]
            },
            {
                'title': _('Address'),
                'icon': 'location_on',
                'fields': [
                    {'field': form['address'], 'col_class': 'col-12'},
                    {'field': form['address_line_2'], 'col_class': 'col-12'},
                    {'field': form['city'], 'col_class': 'col-md-4'},
                    {'field': form['postal_code'], 'col_class': 'col-md-3'},
                    {'field': form['state_province'], 'col_class': 'col-md-2'},
                    {'field': form['country'], 'col_class': 'col-md-3'},
                ]
            },
            {
                'title': _('Contact Information'),
                'icon': 'contact_phone',
                'fields': [
                    {'field': form['phone'], 'col_class': 'col-md-6'},
                    {'field': form['email'], 'col_class': 'col-md-6'},
                ]
            },
            {
                'title': _('Management'),
                'icon': 'admin_panel_settings',
                'fields': [
                    {'field': form['manager'], 'col_class': 'col-md-6'},
                    {'field': form['labor_budget'], 'col_class': 'col-md-6'},
                ]
            },
            {
                'title': _('Geolocation (Optional)'),
                'icon': 'map',
                'fields': [
                    {'field': form['latitude'], 'col_class': 'col-md-6'},
                    {'field': form['longitude'], 'col_class': 'col-md-6'},
                ]
            },
            {
                'title': _('Additional Notes'),
                'icon': 'notes',
                'fields': [
                    {'field': form['notes'], 'col_class': 'col-12'},
                ]
            }
        ]

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        meta = self.get_page_metadata()
        ctx.update(meta)
        form = ctx.get('form') or self.get_form()
        ctx['forms'] = [form]
        ctx['form_sections'] = self.get_form_sections(form)
        return ctx

    def post(self, request, *args, **kwargs):
        if 'pk' in kwargs:
            self.object = self.get_object()
        else:
            self.object = None
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        return self.form_invalid(form)

    def form_valid(self, form):
        """Default save + success message."""
        self.object = form.save()
        messages.success(self.request, _('Location saved successfully.'))
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, _('Please correct the errors below.'))
        return self.render_to_response(self.get_context_data(form=form))

    def get_success_url(self):
        if getattr(self, 'object', None):
            return reverse('employees:location_detail', kwargs={'pk': self.object.pk})
        return reverse('employees:location_list')


# ============================================
# Location Create / Update Views
# ============================================

class LocationCreateView(LocationFormMixin, BreadcrumbMixin, LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Create new location."""

    permission_required = 'employees.add_location'

    def get_breadcrumbs(self):
        """Breadcrumbs for location create."""
        return [
            {'label': _('Dashboard'), 'url': reverse('dashboard:home')},
            {'label': _('Employees'), 'url': reverse('employees:employee_list')},
            {'label': _('Locations'), 'url': reverse('employees:location_list')},
            {'label': _('Create'), 'url': None},
        ]

    def get_page_metadata(self):
        """Page metadata for create view."""
        return {
            'page_title': _('Create Location'),
            'page_subtitle': _('Add a new location to the organization'),
            'cancel_url': reverse_lazy('employees:location_list'),
            'submit_text': _('Create Location'),
            'show_back': True,
        }


class LocationUpdateView(LocationFormMixin, BreadcrumbMixin, LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Update existing location."""

    permission_required = 'employees.change_location'

    def get_breadcrumbs(self):
        """Breadcrumbs for location update."""
        return [
            {'label': _('Dashboard'), 'url': reverse('dashboard:home')},
            {'label': _('Employees'), 'url': reverse('employees:employee_list')},
            {'label': _('Locations'), 'url': reverse('employees:location_list')},
            {'label': self.object.name, 'url': reverse('employees:location_detail', kwargs={'pk': self.object.pk})},
            {'label': _('Edit'), 'url': None},
        ]

    def get_page_metadata(self):
        """Page metadata for update view."""
        return {
            'page_title': _('Edit Location'),
            'page_subtitle': _('Update location information'),
            'cancel_url': reverse_lazy('employees:location_detail', kwargs={'pk': self.object.pk}),
            'submit_text': _('Save Changes'),
            'show_back': True,
        }


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
            {'label': 'Home', 'url': '/'},
            {'label': 'Locations', 'url': reverse('employees:location_list')},
            {'label': self.object.name},  # Active item (no URL)
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
