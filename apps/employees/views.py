"""
Views for employee management.
"""

from django.views.generic import ListView
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.db import transaction
from django.db.models import Q, Count, Case, When, IntegerField, Value
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.utils.safestring import mark_safe
from django.utils import timezone
from datetime import timedelta
import json

from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    ListView, DetailView, CreateView,
    UpdateView, DeleteView
)

from apps.accounts.models import User
from .models import Department, Location, Position, Employee, EmployeeDocument
from .forms import (
    DepartmentForm, EmployeeFilterForm, LocationForm, LocationSearchForm, PositionForm,
    EmployeeUserForm, EmployeeForm, EmployeeDocumentForm,
    EmployeeSearchForm
)


# ============================================
# Employee Views
# ============================================

# apps/employees/views.py - Working version

from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Q
from django.urls import reverse_lazy
from django.utils import timezone
from datetime import timedelta

from .models import Employee, Department, Position
from .forms import EmployeeFilterForm


# ============================================
# Employee List View
# ============================================

class EmployeeListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """
    Display list of employees with filtering and search capabilities.
    """
    model = Employee
    template_name = 'employees/employee_list.html'
    context_object_name = 'employees'
    paginate_by = 20
    permission_required = 'employees.view_employee'
    
    def get_queryset(self):
        """Apply filters and search to queryset."""
        queryset = super().get_queryset().select_related(
            'user', 
            'department', 
            'position'
        )
        
        # Get filter parameters
        search = self.request.GET.get('search', '')
        department = self.request.GET.get('department')
        position = self.request.GET.get('position')
        status = self.request.GET.get('status')
        employment_type = self.request.GET.get('employment_type')
        
        # Apply search
        if search:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(user__email__icontains=search) |
                Q(employee_id__icontains=search)
            )
        
        # Apply filters
        if department:
            queryset = queryset.filter(department_id=department)
        
        if position:
            queryset = queryset.filter(position_id=position)
        
        if status:
            if status == 'active':
                queryset = queryset.filter(is_active=True)
            elif status == 'inactive':
                queryset = queryset.filter(is_active=False)
        
        if employment_type:
            queryset = queryset.filter(employment_type=employment_type)
        
        return queryset.order_by('-created_at')
    
    def get_context_data(self, **kwargs):
        """Add statistics and filter form to context."""
        context = super().get_context_data(**kwargs)
        
        # Get current time
        now = timezone.now()
        
        # Calculate statistics
        total_employees = Employee.objects.filter(is_active=True).count()
        last_month_employees = Employee.objects.filter(
            is_active=True,
            created_at__gte=now - timedelta(days=30)
        ).count()
        
        # Calculate trend (percentage change)
        if total_employees > 0:
            trend = round((last_month_employees / total_employees) * 100, 1)
        else:
            trend = 0
        
        # Add statistics
        context['stats'] = {
            'total_active': total_employees,
            'active_trend': trend,
            'total_departments': Department.objects.filter(is_active=True).count(),
            'total_positions': Position.objects.filter(is_active=True).count(),
            'expiring_certifications': 0,  # Placeholder for now
        }
        
        # Prepare stats cards for the component
        context['stats_cards'] = [
            {
                'title': 'Total Active',
                'value': total_employees,
                'icon': 'people',
                'bg_color': 'primary',
                'trend_value': trend,
                'trend_direction': 'up' if trend > 0 else 'flat',
            },
            {
                'title': 'Departments',
                'value': Department.objects.filter(is_active=True).count(),
                'icon': 'apartment',
                'bg_color': 'success',
            },
            {
                'title': 'Positions',
                'value': Position.objects.filter(is_active=True).count(),
                'icon': 'work',
                'bg_color': 'info',
            },
            {
                'title': 'Total Records',
                'value': self.get_queryset().count(),
                'icon': 'badge',
                'bg_color': 'warning',
            },
        ]
        
        # Add filter form
        context['filter_form'] = EmployeeFilterForm(self.request.GET or None)
        
        # Add breadcrumbs
        context['breadcrumb_items'] = [
            {'title': 'Dashboard', 'url': reverse_lazy('dashboard:home')},
            {'title': 'Employees', 'active': True}
        ]
        
        # Add breadcrumbs - используем name вместо title для совместимости
        context['breadcrumb_items'] = [
            {
                'name': 'Dashboard',
                'url': reverse_lazy('dashboard:home')
            },
            {
                'name': 'Employees',
                'active': True
            }
        ]
        
        # Table columns configuration
        context['table_columns'] = [
            {'title': 'ID', 'width': '10%'},
            {'title': 'Name', 'width': '25%'},
            {'title': 'Department', 'width': '15%'},
            {'title': 'Position', 'width': '15%'},
            {'title': 'Type', 'width': '10%'},
            {'title': 'Rate', 'width': '10%'},
            {'title': 'Status', 'width': '8%'},
            {'title': 'Actions', 'width': '7%', 'class': 'text-end'},
        ]
        
        # Convert employees to table rows format
        table_rows = []
        for employee in context['employees']:
            table_rows.append({
                'id': employee.pk,
                'cells': [
                    {'type': 'strong', 'value': employee.employee_id},
                    {
                        'type': 'avatar',
                        'name': employee.user.get_full_name,
                        'subtitle': employee.user.email,
                        'avatar_url': employee.user.profile_picture.url if employee.user.profile_picture else None
                    },
                    {
                        'type': 'badges' if employee.department else 'text',
                        'badges': [{'text': employee.department.code, 'color': 'secondary'}] if employee.department else None,
                        'text': employee.department.name if employee.department else '-'
                    },
                    {
                        'type': 'badges' if employee.position else 'text',
                        'badges': [{'text': employee.position.code, 'color': 'info'}] if employee.position else None,
                        'text': employee.position.title if employee.position else '-'
                    },
                    {
                        'type': 'badge',
                        'text': employee.get_employment_type_display or 'Full-time',
                        'color': 'light text-dark'
                    },
                    {
                        'type': 'currency',
                        'value': employee.hourly_rate,
                        'currency': 'CHF'
                    },
                    {
                        'type': 'status',
                        'value': employee.is_active,
                        'true_text': 'Active',
                        'false_text': 'Inactive'
                    },
                    {
                        'type': 'actions',
                        'class': 'text-end',
                        'actions': [
                            {
                                'type': 'link',
                                'url': reverse_lazy('employees:employee_detail', kwargs={'pk': employee.pk}),
                                'icon': 'visibility',
                                'title': 'View',
                                'color': 'primary'
                            },
                            {
                                'type': 'link',
                                'url': reverse_lazy('employees:employee_update', kwargs={'pk': employee.pk}),
                                'icon': 'edit',
                                'title': 'Edit',
                                'color': 'secondary'
                            }
                        ]
                    }
                ]
            })
        
        context['table_rows'] = table_rows
        
        # Empty state configuration
        context['empty_state_config'] = {
            'icon': 'people_outline',
            'title': 'No employees found',
            'message': 'Start by adding your first employee or adjust your filters',
            'button_text': 'Add First Employee',
            'button_url': reverse_lazy('employees:employee_create'),
        }
        
        # Add URLs for actions
        context['employees_create_url'] = reverse_lazy('employees:employee_create')
        
        # Add helper properties to employees
        for employee in context['employees']:
            employee.has_expiring_certifications = False  # Placeholder
            employee.get_status_display = 'active' if employee.is_active else 'inactive'
        
        return context

class EmployeeDetailView(LoginRequiredMixin, DetailView):
    """Employee detail view with tabs."""

    model = Employee
    template_name = 'employees/employee_detail.html'
    context_object_name = 'employee'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get active tab from query params
        context['active_tab'] = self.request.GET.get('tab', 'personal')

        # Get employee documents
        context['documents'] = self.object.documents.all().order_by(
            '-created_at')

        # URL for document upload
        context['upload_url'] = reverse_lazy('employees:document_upload', kwargs={
                                             'employee_pk': self.object.pk})

        # Breadcrumbs
        context['breadcrumb_items'] = [
            {'name': _('Employees'), 'url': reverse(
                'employees:employee_list')},
            {'name': self.object.full_name},
        ]

        return context


class EmployeeCreateView(LoginRequiredMixin, CreateView):
    """Create new employee."""

    model = Employee
    template_name = 'employees/employee_form.html'
    form_class = EmployeeForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('Add Employee')
        context['form_action'] = _('Create Employee')
        context['cancel_url'] = reverse_lazy('employees:employee_list')

        # Breadcrumbs
        context['breadcrumb_items'] = [
            {'name': _('Employees'), 'url': reverse(
                'employees:employee_list')},
            {'name': _('Create')},
        ]

        return context

    def form_valid(self, form):
        context = self.get_context_data()
        user_form = context['user_form']

        if user_form.is_valid():
            with transaction.atomic():
                # Create user account
                user = user_form.save(commit=False)
                user.username = user.email
                user.set_password('Password123!')  # Default password
                user.save()

                # Create employee
                employee = form.save(commit=False)
                employee.user = user
                employee.save()

                messages.success(
                    self.request,
                    _(f'Employee {employee.full_name} created successfully. Default password: Password123!')
                )
                return redirect('employees:employee_detail', pk=employee.pk)
        else:
            return self.form_invalid(form)


class EmployeeUpdateView(LoginRequiredMixin, UpdateView):
    model = Employee
    form_class = EmployeeForm
    template_name = 'employees/employee_form.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Create user form instance
        if self.request.POST:
            context['user_form'] = EmployeeUserForm(
                self.request.POST,
                self.request.FILES,
                instance=self.object.user
            )
        else:
            context['user_form'] = EmployeeUserForm(instance=self.object.user)

        context['page_title'] = _('Edit Employee')
        context['form_action'] = _('Save Changes')
        context['cancel_url'] = reverse_lazy(
            'employees:employee_detail', kwargs={'pk': self.object.pk})

        # Breadcrumbs
        context['breadcrumb_items'] = [
            {'name': _('Employees'), 'url': reverse(
                'employees:employee_list')},
            {'name': self.object.full_name, 'url': reverse(
                'employees:employee_detail', kwargs={'pk': self.object.pk})},
            {'name': _('Edit')},
        ]

        return context

    def form_valid(self, form):
        context = self.get_context_data()
        user_form = context['user_form']

        if user_form.is_valid():
            user_form.save()
            messages.success(self.request, _('Employee updated successfully.'))
            return super().form_valid(form)
        else:
            return self.form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('employees:employee_detail', kwargs={'pk': self.object.pk})


class EmployeeDeleteView(LoginRequiredMixin, DeleteView):
    model = Employee
    template_name = 'employees/employee_confirm_delete.html'
    success_url = reverse_lazy('employees:employee_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['cancel_url'] = reverse_lazy(
            'employees:employee_detail', kwargs={'pk': self.object.pk})

        # Prepare HTML messages
        context['message_html'] = mark_safe(
            f'{_("Are you sure you want to delete")} <strong>{self.object.full_name}</strong>?<br>'
            f'{_("This action cannot be undone.")}'
        )

        context['warning_html'] = mark_safe(
            f'{_("This will permanently delete:")}'
            '<ul class="mb-0 mt-2">'
            f'<li>{_("Employee profile and employment history")}</li>'
            f'<li>{_("Associated user account")}</li>'
            f'<li>{_("All uploaded documents")}</li>'
            f'<li>{_("Time clock records (if any)")}</li>'
            '</ul>'
        )

        # Breadcrumbs
        context['breadcrumb_items'] = [
            {'name': _('Employees'), 'url': reverse(
                'employees:employee_list')},
            {'name': self.object.full_name, 'url': reverse(
                'employees:employee_detail', kwargs={'pk': self.object.pk})},
            {'name': _('Delete')},
        ]

        return context

    def form_valid(self, form):
        messages.success(self.request, _('Employee deleted successfully.'))
        return super().form_valid(form)

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
    paginate_by = 12

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
    paginate_by = 12

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
    document = get_object_or_404(
        EmployeeDocument, pk=doc_pk, employee=employee)

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

# class DocumentUploadView(LoginRequiredMixin, CreateView):
#     model = Document
#     form_class = DocumentForm
#     template_name = 'employees/document_upload.html'

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         employee = get_object_or_404(Employee, pk=self.kwargs['employee_pk'])
#         context['employee'] = employee
#         context['page_title'] = _('Upload Document')
#         context['subtitle'] = _('for') + ' ' + employee.full_name  # ← Добавьте эту строку
#         context['cancel_url'] = reverse_lazy('employees:employee_detail', kwargs={'pk': employee.pk}) + '?tab=documents'

#         # Breadcrumbs
#         context['breadcrumb_items'] = [
#             {'name': _('Employees'), 'url': reverse('employees:employee_list')},
#             {'name': employee.full_name, 'url': reverse('employees:employee_detail', kwargs={'pk': employee.pk})},
#             {'name': _('Upload Document')},
#         ]

#         return context

#     def form_valid(self, form):
#         employee = get_object_or_404(Employee, pk=self.kwargs['employee_pk'])
#         form.instance.employee = employee
#         form.instance.uploaded_by = self.request.user
#         messages.success(self.request, _('Document uploaded successfully.'))
#         return super().form_valid(form)

#     def get_success_url(self):
#         return reverse_lazy('employees:employee_detail', kwargs={'pk': self.kwargs['employee_pk']}) + '?tab=documents'


# class DocumentDeleteView(LoginRequiredMixin, DeleteView):
#     model = Document
#     template_name = 'employees/document_confirm_delete.html'

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)
#         context['employee'] = self.object.employee
#         context['cancel_url'] = reverse_lazy('employees:employee_detail', kwargs={'pk': self.object.employee.pk}) + '?tab=documents'

#         # Prepare HTML message
#         context['message_html'] = mark_safe(
#             f'{_("Are you sure you want to delete this document?")} <br>'
#             f'<strong>{self.object.title}</strong>'
#         )

#         context['warning_message'] = _('This will permanently delete the document file. This action cannot be undone.')

#         # Breadcrumbs
#         context['breadcrumb_items'] = [
#             {'name': _('Employees'), 'url': reverse('employees:employee_list')},
#             {'name': self.object.employee.full_name, 'url': reverse('employees:employee_detail', kwargs={'pk': self.object.employee.pk}) + '?tab=documents'},
#             {'name': _('Delete Document')},
#         ]

#         return context

#     def get_success_url(self):
#         messages.success(self.request, _('Document deleted successfully.'))
#         return reverse_lazy('employees:employee_detail', kwargs={'pk': self.object.employee.pk}) + '?tab=documents'

# ============================================
# Location Views (Class-Based)
# ============================================


class LocationListView(LoginRequiredMixin, ListView):
    """List all locations with search and filters."""

    model = Location
    template_name = 'employees/location_list.html'
    context_object_name = 'locations'
    paginate_by = 20  # ← Встроенная пагинация как у Employee

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
