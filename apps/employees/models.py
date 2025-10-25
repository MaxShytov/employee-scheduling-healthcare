"""
Employee management models.
"""

from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django_countries.fields import CountryField
from decimal import Decimal

from apps.core.models import TimeStampedModel, Address
# УДАЛЕНО: from apps.accounts.models import User


# apps/employees/models.py

class Department(TimeStampedModel):
    """
    Department/Unit within the healthcare facility.
    Examples: Emergency, ICU, Cardiology, Surgery, etc.
    """
    
    # English: Core fields
    name = models.CharField(
        _('department name'),
        max_length=100,
        unique=True,
        help_text=_('Full department name')
    )
    
    code = models.CharField(
        _('department code'),
        max_length=20,
        unique=True,
        help_text=_('Short code for the department (e.g., ER, ICU, CARD)')
    )
    
    description = models.TextField(
        _('description'),
        blank=True,
        help_text=_('Detailed department description')
    )
    
    # English: Organizational structure
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_departments',
        verbose_name=_('department manager'),
        help_text=_('User responsible for this department')
    )
    
    # English: Status and validity
    is_active = models.BooleanField(
        _('is active'),
        default=True,
        help_text=_('Whether this department is currently operational')
    )
    
    effective_from = models.DateField(
        _('effective from'),
        null=True,
        blank=True,
        help_text=_('Date when department became operational')
    )
    
    effective_to = models.DateField(
        _('effective to'),
        null=True,
        blank=True,
        help_text=_('Date when department ceased operations')
    )
    
    # English: Additional metadata
    phone_extension = models.CharField(
        _('phone extension'),
        max_length=10,
        blank=True,
        help_text=_('Internal phone extension')
    )
    
    location_notes = models.TextField(
        _('location notes'),
        blank=True,
        help_text=_('Physical location details within facility')
    )
    
    class Meta:
        verbose_name = _('department')
        verbose_name_plural = _('departments')
        ordering = ['name']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.name}"
    
    # ========================================
    # Properties
    # ========================================
    
    @property
    def employee_count(self):
        """Return total number of employees in this department."""
        return self.employees.count()
    
    @property
    def active_employee_count(self):
        """Return number of active employees in this department."""
        return self.employees.filter(is_active=True).count()
    
    @property
    def inactive_employee_count(self):
        """Return number of inactive employees in this department."""
        return self.employees.filter(is_active=False).count()
    
    @property
    def manager_display(self):
        """Return manager full name or dash if none."""
        return self.manager.get_full_name() if self.manager else '—'
    
    # ========================================
    # URL helpers
    # ========================================
    
    def get_absolute_url(self):
        """Return URL for department detail view."""
        from django.urls import reverse
        return reverse('employees:department_detail', kwargs={'pk': self.pk})
    
    def get_edit_url(self):
        """Return URL for department edit view."""
        from django.urls import reverse
        return reverse('employees:department_update', kwargs={'pk': self.pk})
    
    def get_delete_url(self):
        """Return URL for department delete view."""
        from django.urls import reverse
        return reverse('employees:department_delete', kwargs={'pk': self.pk})
    
    # ========================================
    # Component helpers
    # ========================================
    
    def get_card_items(self):
        """
        Returns list of items for info_card component.
        English: Used in detail views and listings.
        """
        items = [
            {
                'icon': 'people',
                'value': self.active_employee_count,
                'label': _('Active Employees')
            }
        ]
        
        if self.inactive_employee_count > 0:
            items.append({
                'icon': 'people_outline',
                'value': self.inactive_employee_count,
                'label': _('Inactive Employees')
            })
        
        if self.manager:
            items.append({
                'icon': 'person',
                'label': _('Manager: %(name)s') % {'name': self.manager.get_full_name()}
            })
        
        return items
    
    def get_stats_summary(self):
        """
        Returns summary statistics for dashboard/overview.
        English: Used in list views and analytics.
        """
        return {
            'total_employees': self.employee_count,
            'active_employees': self.active_employee_count,
            'inactive_employees': self.inactive_employee_count,
            'has_manager': bool(self.manager),
        }


class Position(TimeStampedModel):
    """
    Job position/role for employees.
    Examples: Registered Nurse, Doctor, Physician Assistant, etc.
    """

    # English: Core fields
    title = models.CharField(
        _('position title'),
        max_length=100,
        unique=True,
        help_text=_('Full position title')
    )

    code = models.CharField(
        _('position code'),
        max_length=20,
        unique=True,
        help_text=_('Short code for the position (e.g., RN, MD, PA)')
    )

    description = models.TextField(
        _('description'),
        blank=True,
        help_text=_('Detailed position description')
    )

    # English: Requirements
    requires_certification = models.BooleanField(
        _('requires certification'),
        default=False,
        help_text=_('Does this position require medical certification?')
    )

    # English: Compensation range
    min_hourly_rate = models.DecimalField(
        _('minimum hourly rate (CHF)'),
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text=_('Minimum hourly rate in Swiss Francs')
    )

    max_hourly_rate = models.DecimalField(
        _('maximum hourly rate (CHF)'),
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text=_('Maximum hourly rate in Swiss Francs')
    )

    # English: Status
    is_active = models.BooleanField(
        _('is active'),
        default=True,
        help_text=_('Whether this position is currently in use')
    )

    class Meta:
        verbose_name = _('position')
        verbose_name_plural = _('positions')
        ordering = ['title']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.code} - {self.title}"

    # ========================================
    # Properties
    # ========================================

    @property
    def employee_count(self):
        """Return total number of employees with this position."""
        return self.employees.count()

    @property
    def active_employee_count(self):
        """Return number of active employees with this position."""
        return self.employees.filter(is_active=True).count()

    @property
    def inactive_employee_count(self):
        """Return number of inactive employees with this position."""
        return self.employees.filter(is_active=False).count()

    @property
    def rate_range_display(self):
        """Return formatted hourly rate range."""
        return f"CHF {self.min_hourly_rate:.2f} - {self.max_hourly_rate:.2f}"

    # ========================================
    # URL helpers
    # ========================================

    def get_absolute_url(self):
        """Return URL for position detail view."""
        from django.urls import reverse
        return reverse('employees:position_detail', kwargs={'pk': self.pk})

    def get_edit_url(self):
        """Return URL for position edit view."""
        from django.urls import reverse
        return reverse('employees:position_update', kwargs={'pk': self.pk})

    def get_delete_url(self):
        """Return URL for position delete view."""
        from django.urls import reverse
        return reverse('employees:position_delete', kwargs={'pk': self.pk})


class EmploymentType(models.TextChoices):
    """Employment type choices."""
    FULL_TIME = 'FT', _('Full-time')
    PART_TIME = 'PT', _('Part-time')
    CONTRACT = 'CT', _('Contract')
    TEMPORARY = 'TM', _('Temporary')
    INTERN = 'IN', _('Intern')


class Employee(TimeStampedModel):
    """
    Employee profile linked to User account.
    Contains employment details and work-related information.
    """
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='employee_profile',
        verbose_name=_('user account')
    )
    
    # Employment Information
    employee_id = models.CharField(
        _('employee ID'),
        max_length=20,
        unique=True,
        help_text=_('Unique employee identification number')
    )
    
    department = models.ForeignKey(
        Department,
        on_delete=models.PROTECT,
        related_name='employees',
        verbose_name=_('department')
    )
    
    position = models.ForeignKey(
        Position,
        on_delete=models.PROTECT,
        related_name='employees',
        verbose_name=_('position')
    )
    
    location = models.ForeignKey(
        'Location',
        on_delete=models.PROTECT,
        related_name='employees',
        verbose_name=_('location'),
        help_text=_('Primary work location for this employee')
    )
    
    employment_type = models.CharField(
        _('employment type'),
        max_length=2,
        choices=EmploymentType.choices,
        default=EmploymentType.FULL_TIME
    )
    
    hire_date = models.DateField(
        _('hire date'),
        help_text=_('Date when employee was hired')
    )
    
    termination_date = models.DateField(
        _('termination date'),
        null=True,
        blank=True,
        help_text=_('Date when employment ended')
    )
    
    is_active = models.BooleanField(
        _('is active'),
        default=True,
        help_text=_('Is this employee currently active?')
    )
    
    # Compensation
    hourly_rate = models.DecimalField(
        _('hourly rate (CHF)'),
        max_digits=8,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text=_('Hourly wage rate in Swiss Francs')
    )
    
    # Work Schedule
    weekly_hours = models.DecimalField(
        _('weekly hours'),
        max_digits=5,
        decimal_places=2,
        validators=[
            MinValueValidator(Decimal('0.01')),
            MaxValueValidator(Decimal('168.00'))
        ],
        default=Decimal('42.00'),
        help_text=_('Expected weekly working hours')
    )
    
    # Emergency Contact
    emergency_contact_name = models.CharField(
        _('emergency contact name'),
        max_length=200,
        blank=True
    )
    
    emergency_contact_phone = models.CharField(
        _('emergency contact phone'),
        max_length=20,
        blank=True
    )
    
    emergency_contact_relationship = models.CharField(
        _('relationship'),
        max_length=50,
        blank=True,
        help_text=_('Relationship to employee (spouse, parent, etc.)')
    )
    
    # Additional Information
    notes = models.TextField(
        _('notes'),
        blank=True,
        help_text=_('Internal notes about the employee')
    )
    
    class Meta:
        verbose_name = _('employee')
        verbose_name_plural = _('employees')
        ordering = ['-hire_date', 'user__last_name', 'user__first_name']
        indexes = [
            models.Index(fields=['employee_id']),
            models.Index(fields=['department', 'is_active']),
            models.Index(fields=['position', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.employee_id} - {self.user.get_full_name()}"
    
    @property
    def full_name(self):
        """Return employee's full name."""
        return self.user.get_full_name()
    
    @property
    def email(self):
        """Return employee's email."""
        return self.user.email
    
    @property
    def phone(self):
        """Return employee's phone."""
        return self.user.phone
    
    @property
    def years_of_service(self):
        """Calculate years of service."""
        from django.utils import timezone
        from datetime import date
        
        end_date = self.termination_date or date.today()
        delta = end_date - self.hire_date
        return round(delta.days / 365.25, 1)
    
    @property
    def status_display(self):
        """Return human-readable status."""
        if not self.is_active:
            return _('Inactive')
        if self.termination_date:
            return _('Terminated')
        return _('Active')
    
    def deactivate(self, termination_date=None):
        """Deactivate employee."""
        from django.utils import timezone
        
        self.is_active = False
        self.termination_date = termination_date or timezone.now().date()
        self.save()
    
    def reactivate(self):
        """Reactivate employee."""
        self.is_active = True
        self.termination_date = None
        self.save()


class EmployeeDocument(TimeStampedModel):
    """
    Documents associated with employees (contracts, certificates, etc.).
    """
    
    DOCUMENT_TYPES = [
        ('contract', _('Employment Contract')),
        ('certificate', _('Certification')),
        ('license', _('License')),
        ('resume', _('Resume/CV')),
        ('reference', _('Reference Letter')),
        ('other', _('Other')),
    ]
    
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name=_('employee')
    )
    
    document_type = models.CharField(
        _('document type'),
        max_length=20,
        choices=DOCUMENT_TYPES
    )
    
    title = models.CharField(
        _('title'),
        max_length=200
    )
    
    file = models.FileField(
        _('file'),
        upload_to='employee_documents/%Y/%m/',
        help_text=_('Upload document (PDF, DOCX, JPG, PNG)')
    )
    
    description = models.TextField(
        _('description'),
        blank=True
    )
    
    issue_date = models.DateField(
        _('issue date'),
        null=True,
        blank=True
    )
    
    expiry_date = models.DateField(
        _('expiry date'),
        null=True,
        blank=True,
        help_text=_('When does this document expire?')
    )
    
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='uploaded_documents',
        verbose_name=_('uploaded by')
    )
    
    class Meta:
        verbose_name = _('employee document')
        verbose_name_plural = _('employee documents')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.employee.full_name} - {self.title}"
    
    @property
    def is_expired(self):
        """Check if document is expired."""
        if not self.expiry_date:
            return False
        from django.utils import timezone
        return timezone.now().date() > self.expiry_date
    
    @property
    def days_until_expiry(self):
        """Calculate days until expiry."""
        if not self.expiry_date:
            return None
        from django.utils import timezone
        delta = self.expiry_date - timezone.now().date()
        return delta.days


class Location(TimeStampedModel):
    """
    Physical location/clinic where employees work.
    Represents a healthcare facility, clinic, or office.
    Examples: Geneva Clinic, Lausanne Medical Center, Bern Hospital.
    """

    # English: Core fields
    name = models.CharField(
        _('location name'),
        max_length=100,
        unique=True,
        help_text=_('Full location name')
    )

    code = models.CharField(
        _('location code'),
        max_length=20,
        unique=True,
        help_text=_('Short code for location (e.g., GVA, LAU, BRN)')
    )

    # English: Address relation (NEW - unified address model)
    address_detail = models.ForeignKey(
        'core.Address',
        on_delete=models.PROTECT,
        related_name='locations',
        verbose_name=_('address'),
        null=True,
        blank=True,
        help_text=_('Location address details')
    )

    # English: OLD Address fields (will be removed after migration)
    address = models.CharField(
        _('address'),
        max_length=255,
        blank=True,
        help_text=_('Street address (deprecated - use address_detail)')
    )

    address_line_2 = models.CharField(
        _('address line 2'),
        max_length=255,
        blank=True,
        help_text=_('Apartment, suite, unit, building, floor, etc. (deprecated)')
    )

    city = models.CharField(
        _('city'),
        max_length=100,
        blank=True,
        help_text=_('City name (deprecated - use address_detail)')
    )

    postal_code = models.CharField(
        _('postal code'),
        max_length=20,
        blank=True,
        help_text=_('Postal/ZIP code (deprecated - use address_detail)')
    )

    state_province = models.CharField(
        _('state/province/canton'),
        max_length=100,
        blank=True,
        help_text=_('Administrative level 1 (deprecated - use address_detail)')
    )

    country = models.CharField(
        _('country'),
        max_length=2,
        choices=[
            ('CA', _('Canada')),
            ('CH', _('Switzerland')),
            ('LU', _('Luxembourg')),
            ('MC', _('Monaco')),
        ],
        default='CH',
        blank=True,
        help_text=_('Country code (deprecated - use address_detail)')
    )

    # English: Contact information
    phone = models.CharField(
        _('phone number'),
        max_length=20,
        blank=True,
        help_text=_('Main phone number for this location')
    )

    email = models.EmailField(
        _('email'),
        blank=True,
        help_text=_('Main email address for this location')
    )

    # English: Organizational structure
    manager = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='managed_locations',
        verbose_name=_('location manager'),
        help_text=_('User responsible for this location')
    )

    # English: Status
    is_active = models.BooleanField(
        _('is active'),
        default=True,
        help_text=_('Whether this location is currently operational')
    )

    # English: Additional metadata
    notes = models.TextField(
        _('notes'),
        blank=True,
        help_text=_('Internal notes about this location')
    )

    labor_budget = models.DecimalField(
        _('monthly labor budget (CHF)'),
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text=_('Budget for labor costs per month in Swiss Francs')
    )

    # English: Geolocation (optional - for future use)
    latitude = models.DecimalField(
        _('latitude'),
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text=_('GPS latitude coordinate (optional)')
    )

    longitude = models.DecimalField(
        _('longitude'),
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text=_('GPS longitude coordinate (optional)')
    )

    class Meta:
        verbose_name = _('location')
        verbose_name_plural = _('locations')
        ordering = ['name']
        indexes = [
            models.Index(fields=['code']),
            models.Index(fields=['is_active']),
            models.Index(fields=['city']),
        ]

    def __str__(self):
        return f"{self.code} - {self.name}"

    # ========================================
    # Properties
    # ========================================

    @property
    def full_address(self):
        """Return complete formatted address."""
        if self.address_detail:
            return self.address_detail.full_address
        # Fallback to old fields if address_detail not set
        return f"{self.address}, {self.city} {self.postal_code}, {self.country}"

    @property
    def short_address(self):
        """Return short address without state and country."""
        if self.address_detail:
            return self.address_detail.short_address
        # Fallback
        return f"{self.address}, {self.city} {self.postal_code}"

    @property
    def location_subtitle(self):
        """Return state and country for subtitle display."""
        if self.address_detail:
            return self.address_detail.location_subtitle
        # Fallback
        parts = []
        if self.state_province:
            parts.append(self.state_province)
        if self.country:
            parts.append(self.get_country_display())
        return ", ".join(parts) if parts else ""

    @property
    def google_maps_url(self):
        """Return Google Maps URL if coordinates are available."""
        if self.address_detail:
            return self.address_detail.google_maps_url
        # Fallback
        if self.latitude and self.longitude:
            return f"https://www.google.com/maps?q={self.latitude},{self.longitude}"
        return None

    @property
    def employee_count(self):
        """Return total number of employees at this location."""
        return self.employees.count()

    @property
    def active_employee_count(self):
        """Return number of active employees at this location."""
        return self.employees.filter(is_active=True).count()

    @property
    def inactive_employee_count(self):
        """Return number of inactive employees at this location."""
        return self.employees.filter(is_active=False).count()

    @property
    def country_flag(self):
        """Return emoji flag for the country."""
        if self.address_detail:
            return self.address_detail.country_flag
        # Fallback
        flags = {
            'CH': '🇨🇭',  # Switzerland
            'CA': '🇨🇦',  # Canada
            'LU': '🇱🇺',  # Luxembourg
            'MC': '🇲🇨',  # Monaco
        }
        return flags.get(self.country, '')

    @property
    def country_with_flag(self):
        """Return country name with flag emoji."""
        if self.address_detail:
            return self.address_detail.country_with_flag
        # Fallback
        flag = self.country_flag
        name = self.get_country_display() if self.country else ''
        return f"{flag} {name}" if flag else name

    # ========================================
    # URL helpers
    # ========================================

    def get_absolute_url(self):
        """Return URL for location detail view."""
        from django.urls import reverse
        return reverse('employees:location_detail', kwargs={'pk': self.pk})

    def get_edit_url(self):
        """Return URL for location edit view."""
        from django.urls import reverse
        return reverse('employees:location_update', kwargs={'pk': self.pk})

    def get_delete_url(self):
        """Return URL for location delete view."""
        from django.urls import reverse
        return reverse('employees:location_delete', kwargs={'pk': self.pk})