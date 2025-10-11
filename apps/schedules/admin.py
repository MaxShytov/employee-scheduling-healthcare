from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import Shift, Unavailability, ShiftTemplate, ShiftSwapRequest


@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'employee_display',
        'location',
        'position',
        'start_datetime',
        'end_datetime',
        'duration_display',
        'status_badge',
        'created_at'
    ]
    
    list_filter = [
        'status',
        'location',
        'position',
        'start_datetime',
        'created_at'
    ]
    
    search_fields = [
        'employee__user__first_name',
        'employee__user__last_name',
        'employee__user__email',
        'notes'
    ]
    
    date_hierarchy = 'start_datetime'
    
    fieldsets = (
        (_('Assignment'), {
            'fields': ('employee', 'location', 'position')
        }),
        (_('Schedule'), {
            'fields': ('start_datetime', 'end_datetime', 'break_duration')
        }),
        (_('Status & Notes'), {
            'fields': ('status', 'notes')
        }),
        (_('Metadata'), {
            'fields': ('created_by',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_by']
    
    def employee_display(self, obj):
        if obj.employee:
            return obj.employee.get_full_name()
        return format_html('<span style="color: #999;">Open Shift</span>')
    employee_display.short_description = _('Employee')
    
    def duration_display(self, obj):
        return f"{obj.duration_hours}h"
    duration_display.short_description = _('Duration')
    
    def status_badge(self, obj):
        colors = {
            'draft': '#6c757d',
            'published': '#007bff',
            'approved': '#28a745',
            'completed': '#17a2b8',
            'cancelled': '#dc3545',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = _('Status')
    
    def save_model(self, request, obj, form, change):
        if not change:  # Только при создании
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Unavailability)
class UnavailabilityAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'employee',
        'reason',
        'start_datetime',
        'end_datetime',
        'duration_days',
        'is_recurring',
        'created_at'
    ]
    
    list_filter = [
        'reason',
        'is_recurring',
        'start_datetime'
    ]
    
    search_fields = [
        'employee__user__first_name',
        'employee__user__last_name',
        'notes'
    ]
    
    date_hierarchy = 'start_datetime'
    
    fieldsets = (
        (_('Employee'), {
            'fields': ('employee',)
        }),
        (_('Period'), {
            'fields': ('start_datetime', 'end_datetime', 'reason')
        }),
        (_('Recurrence'), {
            'fields': ('is_recurring', 'recurrence_pattern'),
            'classes': ('collapse',)
        }),
        (_('Notes'), {
            'fields': ('notes',)
        }),
    )


@admin.register(ShiftTemplate)
class ShiftTemplateAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'name',
        'location',
        'position',
        'time_range',
        'duration_display',
        'weekdays_display',
        'is_active'
    ]
    
    list_filter = [
        'is_active',
        'location',
        'position'
    ]
    
    search_fields = [
        'name',
        'location__name',
        'position__name'
    ]
    
    fieldsets = (
        (_('Template Info'), {
            'fields': ('name', 'location', 'position', 'is_active')
        }),
        (_('Time'), {
            'fields': ('start_time', 'end_time', 'break_duration')
        }),
        (_('Recurrence'), {
            'fields': ('days_of_week',)
        }),
        (_('Metadata'), {
            'fields': ('created_by',),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['created_by']
    
    def time_range(self, obj):
        return f"{obj.start_time.strftime('%H:%M')} - {obj.end_time.strftime('%H:%M')}"
    time_range.short_description = _('Time Range')
    
    def duration_display(self, obj):
        return f"{obj.duration_hours}h"
    duration_display.short_description = _('Duration')
    
    def weekdays_display(self, obj):
        days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        if obj.days_of_week:
            return ', '.join([days[i] for i in obj.days_of_week if i < len(days)])
        return '-'
    weekdays_display.short_description = _('Weekdays')
    
    def save_model(self, request, obj, form, change):
        if not change:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ShiftSwapRequest)
class ShiftSwapRequestAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'requesting_employee',
        'target_employee',
        'original_shift_display',
        'status_badge',
        'created_at'
    ]
    
    list_filter = [
        'status',
        'created_at'
    ]
    
    search_fields = [
        'requesting_employee__user__first_name',
        'requesting_employee__user__last_name',
        'target_employee__user__first_name',
        'target_employee__user__last_name'
    ]
    
    date_hierarchy = 'created_at'
    
    fieldsets = (
        (_('Swap Details'), {
            'fields': ('original_shift', 'requesting_employee', 'target_employee')
        }),
        (_('Messages'), {
            'fields': ('request_message', 'response_message')
        }),
        (_('Status'), {
            'fields': ('status', 'approved_by', 'approved_at')
        }),
    )
    
    readonly_fields = ['approved_at']
    
    def original_shift_display(self, obj):
        shift = obj.original_shift
        return f"{shift.location.name} - {shift.start_datetime.strftime('%Y-%m-%d %H:%M')}"
    original_shift_display.short_description = _('Original Shift')
    
    def status_badge(self, obj):
        colors = {
            'pending': '#ffc107',
            'accepted_by_employee': '#17a2b8',
            'rejected_by_employee': '#dc3545',
            'approved': '#28a745',
            'rejected': '#dc3545',
            'completed': '#6c757d',
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 8px; '
            'border-radius: 3px; font-size: 11px;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = _('Status')