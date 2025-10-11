"""
Views for employee management.
"""

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.db import transaction
from django.db.models import Q, Count
from django.http import HttpResponseRedirect
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy, reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    ListView, DetailView, CreateView, 
    UpdateView, DeleteView
)

from apps.accounts.models import User
from .models import Department, Location, Position, Employee, EmployeeDocument
from .forms import (
    DepartmentForm, LocationForm, LocationSearchForm, PositionForm,
    EmployeeUserForm, EmployeeForm, EmployeeDocumentForm,
    EmployeeSearchForm
)



# ============================================
# Employee Views
# ============================================

class EmployeeListView(LoginRequiredMixin, ListView):
    """List all employees with search and filters."""
    
    model = Employee
    template_name = 'employees/employee_list.html'
    context_object_name = 'employees'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = Employee.objects.select_related(
            'user', 'department', 'position'
        ).all()
        
        # Get filter parameters
        search = self.request.GET.get('search', '')
        department_id = self.request.GET.get('department', '')
        position_id = self.request.GET.get('position', '')
        employment_type = self.request.GET.get('employment_type', '')
        status = self.request.GET.get('status', '')
        
        # Apply search
        if search:
            queryset = queryset.filter(
                Q(user__first_name__icontains=search) |
                Q(user__last_name__icontains=search) |
                Q(user__email__icontains=search) |
                Q(employee_id__icontains=search)
            )
        
        # Apply filters
        if department_id:
            queryset = queryset.filter(department_id=department_id)
        
        if position_id:
            queryset = queryset.filter(position_id=position_id)
        
        if employment_type:
            queryset = queryset.filter(employment_type=employment_type)
        
        if status == 'active':
            queryset = queryset.filter(is_active=True)
        elif status == 'inactive':
            queryset = queryset.filter(is_active=False)
        
        return queryset.order_by('-hire_date')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = EmployeeSearchForm(self.request.GET)
        context['total_employees'] = Employee.objects.filter(is_active=True).count()
        context['page_title'] = _('Employees')
        return context


class EmployeeDetailView(LoginRequiredMixin, DetailView):
    """Employee detail view with tabs."""
    
    model = Employee
    template_name = 'employees/employee_detail.html'
    context_object_name = 'employee'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['documents'] = self.object.documents.all()
        context['active_tab'] = self.request.GET.get('tab', 'personal')
        context['page_title'] = self.object.full_name
        return context


class EmployeeCreateView(LoginRequiredMixin, CreateView):
    """Create new employee."""
    
    model = Employee
    template_name = 'employees/employee_form.html'
    form_class = EmployeeForm
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['user_form'] = EmployeeUserForm(self.request.POST, self.request.FILES)
        else:
            context['user_form'] = EmployeeUserForm()
        context['page_title'] = _('Add Employee')
        context['form_action'] = _('Add Employee')
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
    """Update employee information."""
    
    model = Employee
    template_name = 'employees/employee_form.html'
    form_class = EmployeeForm
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['user_form'] = EmployeeUserForm(
                self.request.POST, 
                self.request.FILES,  # ← Важно для загрузки файлов!
                instance=self.object.user
            )
        else:
            context['user_form'] = EmployeeUserForm(instance=self.object.user)
        context['page_title'] = _(f'Edit {self.object.full_name}')
        context['form_action'] = _('Update Employee')
        return context
    
    def form_valid(self, form):
        context = self.get_context_data()
        user_form = context['user_form']
        
        if user_form.is_valid():
            with transaction.atomic():
                user_form.save()
                employee = form.save()
                
                messages.success(
                    self.request,
                    _(f'Employee {employee.full_name} updated successfully.')
                )
                return redirect('employees:employee_detail', pk=employee.pk)
        else:
            return self.form_invalid(form)


class EmployeeDeleteView(LoginRequiredMixin, DeleteView):
    """Delete employee."""
    
    model = Employee
    template_name = 'employees/employee_confirm_delete.html'
    success_url = reverse_lazy('employees:employee_list')
    
    def delete(self, request, *args, **kwargs):
        employee = self.get_object()
        messages.success(
            request,
            _(f'Employee {employee.full_name} deleted successfully.')
        )
        return super().delete(request, *args, **kwargs)


# ============================================
# Department Views
# ============================================

class DepartmentListView(LoginRequiredMixin, ListView):
    """List all departments."""
    
    model = Department
    template_name = 'employees/department_list.html'
    context_object_name = 'departments'
    
    def get_queryset(self):
        return Department.objects.annotate(
            emp_count=Count('employees', filter=Q(employees__is_active=True))
        ).order_by('name')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('Departments')
        return context


class DepartmentCreateView(LoginRequiredMixin, CreateView):
    """Create new department."""
    
    model = Department
    form_class = DepartmentForm
    template_name = 'employees/department_form.html'
    success_url = reverse_lazy('employees:department_list')
    
    def form_valid(self, form):
        messages.success(self.request, _('Department created successfully.'))
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('Add Department')
        return context


class DepartmentUpdateView(LoginRequiredMixin, UpdateView):
    """Update department."""
    
    model = Department
    form_class = DepartmentForm
    template_name = 'employees/department_form.html'
    success_url = reverse_lazy('employees:department_list')
    
    def form_valid(self, form):
        messages.success(self.request, _('Department updated successfully.'))
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _(f'Edit {self.object.name}')
        return context


class DepartmentDeleteView(LoginRequiredMixin, DeleteView):
    """Delete department."""
    
    model = Department
    template_name = 'employees/department_confirm_delete.html'
    success_url = reverse_lazy('employees:department_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Добавить emp_count для использования в template
        context['emp_count'] = Employee.objects.filter(
            department=self.object, 
            is_active=True
        ).count()
        return context
    
    def delete(self, request, *args, **kwargs):
        department = self.get_object()
        messages.success(request, _(f'Department {department.name} deleted.'))
        return super().delete(request, *args, **kwargs)

# ============================================
# Position Views
# ============================================

class PositionListView(LoginRequiredMixin, ListView):
    """List all positions."""
    
    model = Position
    template_name = 'employees/position_list.html'
    context_object_name = 'positions'
    
    def get_queryset(self):
        return Position.objects.annotate(
            emp_count=Count('employees', filter=Q(employees__is_active=True))
        ).order_by('title')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('Positions')
        return context


class PositionCreateView(LoginRequiredMixin, CreateView):
    """Create new position."""
    
    model = Position
    form_class = PositionForm
    template_name = 'employees/position_form.html'
    success_url = reverse_lazy('employees:position_list')
    
    def form_valid(self, form):
        messages.success(self.request, _('Position created successfully.'))
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('Add Position')
        return context


class PositionUpdateView(LoginRequiredMixin, UpdateView):
    """Update position."""
    
    model = Position
    form_class = PositionForm
    template_name = 'employees/position_form.html'
    success_url = reverse_lazy('employees:position_list')
    
    def form_valid(self, form):
        messages.success(self.request, _('Position updated successfully.'))
        return super().form_valid(form)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _(f'Edit {self.object.title}')
        return context


class PositionDeleteView(LoginRequiredMixin, DeleteView):
    """Delete position."""
    
    model = Position
    template_name = 'employees/position_confirm_delete.html'
    success_url = reverse_lazy('employees:position_list')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Добавить emp_count для использования в template
        context['emp_count'] = Employee.objects.filter(
            position=self.object, 
            is_active=True
        ).count()
        return context
    
    def delete(self, request, *args, **kwargs):
        position = self.get_object()
        messages.success(request, _(f'Position {position.title} deleted.'))
        return super().delete(request, *args, **kwargs)

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
            url = reverse('employees:employee_detail', kwargs={'pk': employee.pk}) + '?tab=documents'
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
    document = get_object_or_404(EmployeeDocument, pk=doc_pk, employee=employee)
    
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
        context['total_locations'] = Location.objects.filter(is_active=True).count()
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
            _('Location "{}" has been created successfully.').format(form.instance.name)
        )
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('employees:location_detail', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('Create New Location')
        context['form_action'] = _('Create Location')
        return context


class LocationUpdateView(LoginRequiredMixin, UpdateView):
    """Update existing location."""
    
    model = Location
    form_class = LocationForm
    template_name = 'employees/location_form.html'
    
    def form_valid(self, form):
        messages.success(
            self.request,
            _('Location "{}" has been updated successfully.').format(form.instance.name)
        )
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse('employees:location_detail', kwargs={'pk': self.object.pk})
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _(f'Edit {self.object.name}')
        context['form_action'] = _('Update Location')
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