from django.conf import settings
from django.views.generic import ListView

class BaseListView(ListView):
    """
    Base list view with default pagination and common mixins.
    English: All project list views should inherit from this.
    """
    paginate_by = getattr(settings, 'DEFAULT_PAGINATE_BY', 25)
    
    def get_paginate_by(self, queryset):
        """Allow per-view override via pagination_size attribute."""
        if hasattr(self, 'pagination_size'):
            return self.pagination_size
        return self.paginate_by