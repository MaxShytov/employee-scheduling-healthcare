"""
Core models - base models used across the application.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _


class TimeStampedModel(models.Model):
    """
    Abstract base model that provides self-updating
    'created_at' and 'updated_at' fields.
    """
    created_at = models.DateTimeField(
        _('created at'),
        auto_now_add=True,
        help_text=_('Date and time when the record was created')
    )
    updated_at = models.DateTimeField(
        _('updated at'),
        auto_now=True,
        help_text=_('Date and time when the record was last updated')
    )

    class Meta:
        abstract = True
        ordering = ['-created_at']


class ActiveManager(models.Manager):
    """Manager that returns only active (non-deleted) records."""
    
    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class SoftDeleteModel(TimeStampedModel):
    """
    Abstract base model that provides soft delete functionality.
    Records are marked as inactive instead of being deleted.
    """
    is_active = models.BooleanField(
        _('active'),
        default=True,
        help_text=_('Designates whether this record should be treated as active.')
    )
    deleted_at = models.DateTimeField(
        _('deleted at'),
        null=True,
        blank=True,
        help_text=_('Date and time when the record was soft deleted')
    )

    objects = models.Manager()  # Default manager
    active_objects = ActiveManager()  # Manager for active records only

    class Meta:
        abstract = True

    def delete(self, using=None, keep_parents=False, hard=False):
        """
        Soft delete by default. Pass hard=True for actual deletion.
        """
        if hard:
            super().delete(using=using, keep_parents=keep_parents)
        else:
            from django.utils import timezone
            self.is_active = False
            self.deleted_at = timezone.now()
            self.save()

    def restore(self):
        """Restore a soft-deleted record."""
        self.is_active = True
        self.deleted_at = None
        self.save()


class Address(TimeStampedModel):
    """
    Reusable address model for locations, employees, patients, etc.
    Supports international addresses with Swiss-specific features.
    """

    COUNTRY_CHOICES = [
        ('CH', _('Switzerland')),
        ('CA', _('Canada')),
        ('LU', _('Luxembourg')),
        ('MC', _('Monaco')),
    ]

    # Street address
    address = models.CharField(
        _('street address'),
        max_length=255,
        help_text=_('Street name and number')
    )
    address_line_2 = models.CharField(
        _('address line 2'),
        max_length=255,
        blank=True,
        help_text=_('Apartment, suite, unit, building, floor, etc. (optional)')
    )

    # City and postal code
    city = models.CharField(
        _('city'),
        max_length=100
    )
    postal_code = models.CharField(
        _('postal code'),
        max_length=20
    )

    # State/Province/Canton (administrative level 1)
    state_province = models.CharField(
        _('state/province/canton'),
        max_length=100,
        blank=True,
        help_text=_('Administrative level 1: State/Province/Canton code (e.g., VD, QC, NY)')
    )

    # Country
    country = models.CharField(
        _('country'),
        max_length=2,
        choices=COUNTRY_CHOICES,
        default='CH'
    )

    # Geolocation (optional)
    latitude = models.DecimalField(
        _('latitude'),
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text=_('Latitude coordinate for map display')
    )
    longitude = models.DecimalField(
        _('longitude'),
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        help_text=_('Longitude coordinate for map display')
    )

    class Meta:
        verbose_name = _('address')
        verbose_name_plural = _('addresses')
        ordering = ['country', 'city', 'address']
        indexes = [
            models.Index(fields=['country', 'city']),
            models.Index(fields=['postal_code']),
        ]

    def __str__(self):
        """Return formatted address string."""
        return self.full_address

    @property
    def country_flag(self):
        """Return emoji flag for the country."""
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
        flag = self.country_flag
        name = self.get_country_display()
        return f"{flag} {name}" if flag else name

    @property
    def full_address(self):
        """
        Return full address in single line format:
        Street, Address Line 2, City PostalCode, State/Province, CountryCode
        """
        address_parts = []

        # Add street address (line 1 and line 2 if present)
        if self.address:
            street = self.address
            if self.address_line_2:
                street = f"{street}, {self.address_line_2}"
            address_parts.append(street)

        # Add city with postal code
        if self.city:
            city_part = f"{self.city} {self.postal_code}" if self.postal_code else self.city
            address_parts.append(city_part)

        # Add state/province if present
        if self.state_province:
            address_parts.append(self.state_province)

        # Add country code
        if self.country:
            address_parts.append(self.country)

        return ", ".join(address_parts) if address_parts else ""

    @property
    def google_maps_url(self):
        """Return Google Maps URL if coordinates are available."""
        if self.latitude and self.longitude:
            return f"https://www.google.com/maps?q={self.latitude},{self.longitude}"
        return None

    @property
    def short_address(self):
        """Return short address without state and country: Street, City PostalCode"""
        address_parts = []

        if self.address:
            street = self.address
            if self.address_line_2:
                street = f"{street}, {self.address_line_2}"
            address_parts.append(street)

        if self.city:
            city_part = f"{self.city} {self.postal_code}" if self.postal_code else self.city
            address_parts.append(city_part)

        return ", ".join(address_parts) if address_parts else ""

    @property
    def location_subtitle(self):
        """Return state and country for subtitle display."""
        subtitle_parts = []
        if self.state_province:
            subtitle_parts.append(self.state_province)
        if self.country:
            subtitle_parts.append(self.get_country_display())
        return ", ".join(subtitle_parts) if subtitle_parts else ""