from django.contrib import admin
from .models import Address


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    """Admin interface for Address model."""

    list_display = ['id', 'address', 'city', 'postal_code', 'state_province', 'country', 'created_at']
    list_filter = ['country', 'state_province']
    search_fields = ['address', 'city', 'postal_code']
    ordering = ['country', 'city', 'address']

    fieldsets = (
        ('Street Address', {
            'fields': ('address', 'address_line_2')
        }),
        ('City & Region', {
            'fields': ('city', 'postal_code', 'state_province', 'country')
        }),
        ('Geolocation', {
            'fields': ('latitude', 'longitude'),
            'classes': ('collapse',)
        }),
    )
