"""
Admin interface for employees app.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse

from .models import Department, Position, Employee, EmployeeDocument


@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    """Admin interface for Department model."""
    
    list_display = (
        'code',
        'name',
        'manager_link',
        'employee_count_display',
        'is_active',
        'created_at'
    )
    list_filter = ('is_active', 'created_at')
    search_fields = ('name', 'code', 'description')
    ordering = ('name',)
    
    fieldsets = (
        (None, {
            'fields': ('name', 'code', 'description')
        }),
        (_('Management'), {
            'fields': ('manager', 'is_active')
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def manager_link(self, obj):
        """Display link to manager."""
        if obj.manager:
            url = reverse('admin:accounts_user_change', args=[obj.manager.pk])
            return format_html('<a href="{}">{}</a>', url, obj.manager.get_full_name())
        return '-'
    manager_link.short_description = _('Manager')
    
    def employee_count_display(self, obj):
        """Display employee count."""
        count = obj.employee_count
        if count > 0:
            return format_html('<strong>{}</strong>', count)
        return count
    employee_count_display.short_description = _('Employees')


@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    """Admin interface for Position model."""
    
    list_display = (
        'code',
        'title',
        'rate_range_display',
        'requires_certification',
        'employee_count_display',
        'is_active',
        'created_at'
    )
    list_filter = ('requires_certification', 'is_active', 'created_at')
    search_fields = ('title', 'code', 'description')
    ordering = ('title',)
    
    fieldsets = (
        (None, {
            'fields': ('title', 'code', 'description')
        }),
        (_('Requirements'), {
            'fields': ('requires_certification',)
        }),
        (_('Compensation'), {
            'fields': ('min_hourly_rate', 'max_hourly_rate')
        }),
        (_('Status'), {
            'fields': ('is_active',)
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    
    def rate_range_display(self, obj):
        """Display hourly rate range."""
        min_rate = float(obj.min_hourly_rate)
        max_rate = float(obj.max_hourly_rate)
        return 'CHF {:.2f} - {:.2f}'.format(min_rate, max_rate)
    rate_range_display.short_description = _('Rate Range')
    
    def employee_count_display(self, obj):
        """Display employee count."""
        count = obj.employee_count
        if count > 0:
            return format_html('<strong>{}</strong>', count)
        return count
    employee_count_display.short_description = _('Employees')


class EmployeeDocumentInline(admin.TabularInline):
    """Inline for employee documents."""
    model = EmployeeDocument
    extra = 0
    fields = ('document_type', 'title', 'file', 'expiry_date', 'uploaded_by')
    readonly_fields = ('uploaded_by',)


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    """Admin interface for Employee model."""
    
    list_display = (
        'employee_id',
        'user_link',
        'department',
        'position',
        'employment_type',
        'hourly_rate_display',
        'status_badge',
        'hire_date'
    )
    list_filter = (
        'is_active',
        'employment_type',
        'department',
        'position',
        'hire_date'
    )
    search_fields = (
        'employee_id',
        'user__first_name',
        'user__last_name',
        'user__email'
    )
    ordering = ('-hire_date',)
    date_hierarchy = 'hire_date'
    
    fieldsets = (
        (_('User Account'), {
            'fields': ('user',)
        }),
        (_('Employment Information'), {
            'fields': (
                'employee_id',
                'department',
                'position',
                'employment_type',
                'hire_date',
                'termination_date',
                'is_active'
            )
        }),
        (_('Compensation'), {
            'fields': ('hourly_rate', 'weekly_hours')
        }),
        (_('Emergency Contact'), {
            'fields': (
                'emergency_contact_name',
                'emergency_contact_phone',
                'emergency_contact_relationship'
            ),
            'classes': ('collapse',)
        }),
        (_('Additional Information'), {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        (_('Metadata'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')
    inlines = [EmployeeDocumentInline]
    
    def user_link(self, obj):
        """Display link to user."""
        url = reverse('admin:accounts_user_change', args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.full_name)
    user_link.short_description = _('Name')
    
    def hourly_rate_display(self, obj):
        """Display hourly rate."""
        rate = float(obj.hourly_rate)
        return 'CHF {:.2f}'.format(rate)
    hourly_rate_display.short_description = _('Hourly Rate')
    
    def status_badge(self, obj):
        """Display status with colored badge."""
        if obj.is_active:
            color = 'green'
            text = 'Active'
        else:
            color = 'red'
            text = 'Inactive'
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px; font-weight: bold;">{}</span>',
            color,
            text
        )
    status_badge.short_description = _('Status')


@admin.register(EmployeeDocument)
class EmployeeDocumentAdmin(admin.ModelAdmin):
    """Admin interface for EmployeeDocument model."""
    
    list_display = (
        'title',
        'employee_link',
        'document_type',
        'issue_date',
        'expiry_date',
        'expiry_status',
        'uploaded_by',
        'created_at'
    )
    list_filter = ('document_type', 'issue_date', 'expiry_date')
    search_fields = (
        'title',
        'employee__user__first_name',
        'employee__user__last_name',
        'employee__employee_id'
    )
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (None, {
            'fields': ('employee', 'document_type', 'title', 'description')
        }),
        (_('File'), {
            'fields': ('file',)
        }),
        (_('Dates'), {
            'fields': ('issue_date', 'expiry_date')
        }),
        (_('Metadata'), {
            'fields': ('uploaded_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('uploaded_by', 'created_at', 'updated_at')
    
    def employee_link(self, obj):
        """Display link to employee."""
        url = reverse('admin:employees_employee_change', args=[obj.employee.pk])
        return format_html('<a href="{}">{}</a>', url, obj.employee.full_name)
    employee_link.short_description = _('Employee')
    
    def expiry_status(self, obj):
        """Display expiry status with color."""
        if not obj.expiry_date:
            return '-'
        
        days = obj.days_until_expiry
        
        if days < 0:
            return format_html(
                '<span style="color: red; font-weight: bold;">Expired</span>'
            )
        elif days <= 30:
            return format_html(
                '<span style="color: orange; font-weight: bold;">Expires in {} days</span>',
                days
            )
        else:
            return format_html(
                '<span style="color: green;">Valid ({} days)</span>',
                days
            )
    expiry_status.short_description = _('Status')
    
    def save_model(self, request, obj, form, change):
        """Save model and set uploaded_by."""
        if not change:  # Only on creation
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)