"""
Admin configuration for accounts app.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html

from .models import User, PasswordResetToken


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Custom User admin interface.
    """
    list_display = (
        'email', 
        'get_full_name', 
        'profile_picture_preview',
        'is_staff', 
        'is_active',
        'date_joined'
    )
    list_filter = ('is_staff', 'is_active', 'country', 'date_joined')
    search_fields = ('email', 'first_name', 'last_name', 'username')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {
            'fields': ('email', 'username', 'password')
        }),
        (_('Personal Info'), {
            'fields': ('first_name', 'last_name', 'date_of_birth', 'profile_picture')
        }),
        (_('Contact Information'), {
            'fields': ('phone', 'country')
        }),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        (_('Important Dates'), {
            'fields': ('last_login', 'date_joined')
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 
                'username',
                'first_name', 
                'last_name',
                'password1', 
                'password2',
                'is_staff',
                'is_active'
            ),
        }),
    )
    
    readonly_fields = ('date_joined', 'last_login')
    
    def profile_picture_preview(self, obj):
        """Display profile picture thumbnail in admin."""
        if obj.profile_picture:
            return format_html(
                '<img src="{}" style="width: 40px; height: 40px; border-radius: 50%; object-fit: cover;" />',
                obj.profile_picture.url
            )
        return format_html(
            '<div style="width: 40px; height: 40px; border-radius: 50%; background-color: #667eea; color: white; display: flex; align-items: center; justify-content: center; font-weight: bold;">{}</div>',
            obj.initials
        )
    profile_picture_preview.short_description = _('Picture')


@admin.register(PasswordResetToken)
class PasswordResetTokenAdmin(admin.ModelAdmin):
    """
    Admin interface for password reset tokens.
    """
    list_display = ('user', 'is_used', 'is_valid_status', 'created_at', 'expires_at')
    list_filter = ('is_used', 'created_at', 'expires_at')
    search_fields = ('user__email', 'token')
    readonly_fields = ('user', 'token', 'created_at', 'updated_at', 'expires_at')
    
    def is_valid_status(self, obj):
        """Display if token is valid."""
        if obj.is_valid():
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Valid</span>'
            )
        return format_html(
            '<span style="color: red; font-weight: bold;">✗ Invalid</span>'
        )
    is_valid_status.short_description = _('Status')
    
    def has_add_permission(self, request):
        """Disable manual creation of tokens."""
        return False