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