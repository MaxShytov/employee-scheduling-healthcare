"""
User model and authentication models.
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_countries.fields import CountryField

from apps.core.models import TimeStampedModel
from apps.core.validators import validate_swiss_phone


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser.
    Uses email as the primary identifier instead of username.
    """

    # Override email to make it unique and required
    email = models.EmailField(
        _('email address'),
        unique=True,
        error_messages={
            'unique': _("A user with that email already exists."),
        }
    )

    # Additional fields
    phone = models.CharField(
        _('phone number'),
        max_length=20,
        blank=True,
        validators=[validate_swiss_phone],
        help_text=_('Swiss phone format: +41 XX XXX XX XX or 0XX XXX XX XX')
    )

    country = CountryField(
        _('country'),
        default='CH',  # Switzerland
        blank_label=_('Select country')
    )

    date_of_birth = models.DateField(
        _('date of birth'),
        null=True,
        blank=True
    )

    profile_picture = models.ImageField(
        _('profile picture'),
        upload_to='profile_pictures/%Y/%m/',
        null=True,
        blank=True
    )

    # Use email as username
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        ordering = ['-date_joined']

    def __str__(self):
        return self.email

    def get_full_name(self):
        """Return the full name."""
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name or self.email

    def get_short_name(self):
        """Return the short name."""
        return self.first_name or self.email.split('@')[0]

    @property
    def initials(self):
        """Return user initials (e.g., 'JD' for John Doe)."""
        if self.first_name and self.last_name:
            return f"{self.first_name[0]}{self.last_name[0]}".upper()
        return self.email[0].upper()

    @property
    def country_with_flag(self):
        """Return country name with flag emoji."""
        if self.country:
            return f"{self.country.flag} {self.country.name}"
        return ''

    @property
    def profile_picture_url(self):
        """
        Get profile picture URL safely.
        English: Returns URL if file exists, None otherwise.
        Prevents errors when file is deleted from filesystem.

        Returns:
            str or None: Profile picture URL or None
        """
        if not self.profile_picture:
            return None

        try:
            # English: Check if file physically exists in storage
            if self.profile_picture.storage.exists(self.profile_picture.name):
                return self.profile_picture.url
        except Exception:
            # English: Catch any storage errors (permissions, missing storage, etc.)
            pass

        return None

    def get_avatar_url(self, default=None):
        """
        Get avatar URL with fallback to default.
        English: Returns profile picture URL or default avatar image.

        Args:
            default: Custom default avatar URL (optional)

        Returns:
            str: Avatar URL (profile picture or default)
        """
        from django.conf import settings

        # English: Try to get profile picture URL
        url = self.profile_picture_url
        if url:
            return url

        # English: Use provided default or system default
        if default:
            return default

        return f"{settings.STATIC_URL}images/default-avatar.png"

    def has_profile_picture(self):
        """
        Check if user has a valid profile picture.
        English: Returns True if profile picture exists in filesystem.

        Returns:
            bool: True if valid profile picture exists
        """
        return self.profile_picture_url is not None

    def delete_profile_picture(self):
        """
        Delete profile picture file and clear field.
        English: Safely removes profile picture from storage and database.
        """
        if self.profile_picture:
            try:
                # English: Delete file from storage
                self.profile_picture.delete(save=False)
            except Exception:
                # English: File might already be deleted
                pass

            # English: Clear database field
            self.profile_picture = None
            self.save(update_fields=['profile_picture'])


class PasswordResetToken(TimeStampedModel):
    """
    Model to store password reset tokens.
    Tokens expire after 24 hours.
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='password_reset_tokens',
        verbose_name=_('user')
    )

    token = models.CharField(
        _('token'),
        max_length=100,
        unique=True
    )

    is_used = models.BooleanField(
        _('is used'),
        default=False
    )

    expires_at = models.DateTimeField(
        _('expires at')
    )

    class Meta:
        verbose_name = _('password reset token')
        verbose_name_plural = _('password reset tokens')
        ordering = ['-created_at']

    def __str__(self):
        return f"Reset token for {self.user.email}"

    def is_valid(self):
        """Check if token is still valid."""
        from django.utils import timezone
        return not self.is_used and timezone.now() < self.expires_at
