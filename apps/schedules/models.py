from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from datetime import timedelta

from apps.core.models import TimeStampedModel
from apps.employees.models import Employee, Location, Position


class Shift(TimeStampedModel):
    """
    Модель смены сотрудника.
    Nullable employee для открытых смен (не назначенных).
    """
    
    STATUS_CHOICES = [
        ('draft', _('Draft')),
        ('published', _('Published')),
        ('approved', _('Approved')),
        ('completed', _('Completed')),
        ('cancelled', _('Cancelled')),
    ]
    
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='shifts',
        null=True,
        blank=True,
        verbose_name=_('Employee'),
        help_text=_('Leave empty for open shifts')
    )
    
    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name='shifts',
        verbose_name=_('Location')
    )
    
    position = models.ForeignKey(
        Position,
        on_delete=models.CASCADE,
        related_name='shifts',
        verbose_name=_('Position')
    )
    
    start_datetime = models.DateTimeField(
        verbose_name=_('Start Date & Time')
    )
    
    end_datetime = models.DateTimeField(
        verbose_name=_('End Date & Time')
    )
    
    break_duration = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Break Duration (minutes)'),
        help_text=_('Duration of unpaid break in minutes')
    )
    
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name=_('Status')
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name=_('Notes'),
        help_text=_('Internal notes for this shift')
    )
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='created_shifts',
        verbose_name=_('Created By')
    )
    
    class Meta:
        verbose_name = _('Shift')
        verbose_name_plural = _('Shifts')
        ordering = ['-start_datetime']
        indexes = [
            models.Index(fields=['start_datetime', 'end_datetime']),
            models.Index(fields=['location', 'start_datetime']),
            models.Index(fields=['employee', 'start_datetime']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        employee_name = self.employee.get_full_name() if self.employee else _('Open Shift')
        return f"{employee_name} - {self.location.name} - {self.start_datetime.strftime('%Y-%m-%d %H:%M')}"
    
    def clean(self):
        """Валидация модели"""
        errors = {}
        
        # Проверка: конец после начала
        if self.end_datetime <= self.start_datetime:
            errors['end_datetime'] = _('End time must be after start time')
        
        # Проверка: смена не слишком длинная (максимум 24 часа)
        if self.end_datetime - self.start_datetime > timedelta(hours=24):
            errors['end_datetime'] = _('Shift cannot be longer than 24 hours')
        
        # Проверка: break не больше длительности смены
        shift_duration = (self.end_datetime - self.start_datetime).total_seconds() / 60
        if self.break_duration >= shift_duration:
            errors['break_duration'] = _('Break duration cannot be longer than shift duration')
        
        # Проверка overlap только если employee назначен
        if self.employee:
            overlapping_shifts = Shift.objects.filter(
                employee=self.employee,
                start_datetime__lt=self.end_datetime,
                end_datetime__gt=self.start_datetime
            ).exclude(pk=self.pk).exclude(status='cancelled')
            
            if overlapping_shifts.exists():
                errors['employee'] = _('This employee already has a shift during this time period')
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def duration_hours(self):
        """Длительность смены в часах (с учетом перерыва)"""
        total_minutes = (self.end_datetime - self.start_datetime).total_seconds() / 60
        work_minutes = total_minutes - self.break_duration
        return round(work_minutes / 60, 2)
    
    @property
    def is_open_shift(self):
        """Проверка, является ли смена открытой (без назначенного сотрудника)"""
        return self.employee is None
    
    @property
    def is_past(self):
        """Проверка, прошла ли смена"""
        return self.end_datetime < timezone.now()
    
    @property
    def is_ongoing(self):
        """Проверка, идет ли смена сейчас"""
        now = timezone.now()
        return self.start_datetime <= now <= self.end_datetime


class Unavailability(TimeStampedModel):
    """
    Модель недоступности сотрудника.
    Используется для отпусков, больничных, личных дел.
    """
    
    REASON_CHOICES = [
        ('vacation', _('Vacation')),
        ('sick', _('Sick Leave')),
        ('personal', _('Personal')),
        ('training', _('Training')),
        ('other', _('Other')),
    ]
    
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='unavailabilities',
        verbose_name=_('Employee')
    )
    
    start_datetime = models.DateTimeField(
        verbose_name=_('Start Date & Time')
    )
    
    end_datetime = models.DateTimeField(
        verbose_name=_('End Date & Time')
    )
    
    reason = models.CharField(
        max_length=20,
        choices=REASON_CHOICES,
        default='personal',
        verbose_name=_('Reason')
    )
    
    is_recurring = models.BooleanField(
        default=False,
        verbose_name=_('Recurring'),
        help_text=_('Is this a recurring unavailability?')
    )
    
    recurrence_pattern = models.JSONField(
        null=True,
        blank=True,
        verbose_name=_('Recurrence Pattern'),
        help_text=_('JSON pattern for recurring unavailability (e.g., every Monday)')
    )
    
    notes = models.TextField(
        blank=True,
        verbose_name=_('Notes')
    )
    
    class Meta:
        verbose_name = _('Unavailability')
        verbose_name_plural = _('Unavailabilities')
        ordering = ['-start_datetime']
        indexes = [
            models.Index(fields=['employee', 'start_datetime']),
            models.Index(fields=['start_datetime', 'end_datetime']),
        ]
    
    def __str__(self):
        return f"{self.employee.get_full_name()} - {self.get_reason_display()} - {self.start_datetime.strftime('%Y-%m-%d')}"
    
    def clean(self):
        """Валидация модели"""
        errors = {}
        
        if self.end_datetime <= self.start_datetime:
            errors['end_datetime'] = _('End time must be after start time')
        
        # Проверка overlap с другими unavailabilities
        overlapping = Unavailability.objects.filter(
            employee=self.employee,
            start_datetime__lt=self.end_datetime,
            end_datetime__gt=self.start_datetime
        ).exclude(pk=self.pk)
        
        if overlapping.exists():
            errors['employee'] = _('This employee already has unavailability during this period')
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)
    
    @property
    def duration_days(self):
        """Длительность в днях"""
        return (self.end_datetime - self.start_datetime).days


class ShiftTemplate(TimeStampedModel):
    """
    Шаблон смены для быстрого создания повторяющихся смен.
    """
    
    name = models.CharField(
        max_length=100,
        verbose_name=_('Template Name')
    )
    
    location = models.ForeignKey(
        Location,
        on_delete=models.CASCADE,
        related_name='shift_templates',
        verbose_name=_('Location')
    )
    
    position = models.ForeignKey(
        Position,
        on_delete=models.CASCADE,
        related_name='shift_templates',
        verbose_name=_('Position')
    )
    
    start_time = models.TimeField(
        verbose_name=_('Start Time'),
        help_text=_('Time only, without date')
    )
    
    end_time = models.TimeField(
        verbose_name=_('End Time'),
        help_text=_('Time only, without date')
    )
    
    break_duration = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Break Duration (minutes)')
    )
    
    days_of_week = models.JSONField(
        default=list,
        verbose_name=_('Days of Week'),
        help_text=_('List of weekday numbers: 0=Monday, 6=Sunday')
    )
    
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Active')
    )
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='shift_templates',
        verbose_name=_('Created By')
    )
    
    class Meta:
        verbose_name = _('Shift Template')
        verbose_name_plural = _('Shift Templates')
        ordering = ['name']
    
    def __str__(self):
        return f"{self.name} - {self.location.name} - {self.position.name}"
    
    @property
    def duration_hours(self):
        """Длительность шаблона в часах"""
        from datetime import datetime, timedelta
        start = datetime.combine(datetime.today(), self.start_time)
        end = datetime.combine(datetime.today(), self.end_time)
        
        # Если end_time меньше start_time, значит смена переходит на следующий день
        if end < start:
            end += timedelta(days=1)
        
        total_minutes = (end - start).total_seconds() / 60 - self.break_duration
        return round(total_minutes / 60, 2)


class ShiftSwapRequest(TimeStampedModel):
    """
    Запрос на обмен сменами между сотрудниками.
    """
    
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('accepted_by_employee', _('Accepted by Employee')),
        ('rejected_by_employee', _('Rejected by Employee')),
        ('approved', _('Approved by Manager')),
        ('rejected', _('Rejected by Manager')),
        ('completed', _('Completed')),
    ]
    
    original_shift = models.ForeignKey(
        Shift,
        on_delete=models.CASCADE,
        related_name='swap_requests_as_original',
        verbose_name=_('Original Shift')
    )
    
    requesting_employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='initiated_swap_requests',
        verbose_name=_('Requesting Employee'),
        help_text=_('Employee who wants to swap their shift')
    )
    
    target_employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='received_swap_requests',
        verbose_name=_('Target Employee'),
        help_text=_('Employee who is asked to take the shift')
    )
    
    status = models.CharField(
        max_length=30,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name=_('Status')
    )
    
    request_message = models.TextField(
        blank=True,
        verbose_name=_('Request Message'),
        help_text=_('Message from requesting employee')
    )
    
    response_message = models.TextField(
        blank=True,
        verbose_name=_('Response Message'),
        help_text=_('Response from target employee or manager')
    )
    
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_swaps',
        verbose_name=_('Approved By')
    )
    
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Approved At')
    )
    
    class Meta:
        verbose_name = _('Shift Swap Request')
        verbose_name_plural = _('Shift Swap Requests')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Swap: {self.requesting_employee} → {self.target_employee} - {self.get_status_display()}"
    
    def clean(self):
        """Валидация"""
        errors = {}
        
        # Requesting employee должен быть владельцем original_shift
        if self.original_shift.employee != self.requesting_employee:
            errors['requesting_employee'] = _('Requesting employee must be assigned to the original shift')
        
        # Target employee не должен быть requesting employee
        if self.requesting_employee == self.target_employee:
            errors['target_employee'] = _('Cannot swap shift with yourself')
        
        if errors:
            raise ValidationError(errors)
    
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)