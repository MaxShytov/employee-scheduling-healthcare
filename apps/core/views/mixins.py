# apps/core/views/mixins.py
from typing import Optional, Type
from django.db import models
from apps.core.filters import FilterSet


class FilterMixin:
    """
    Mixin for ListView to add declarative filtering.
    
    Automatically adds to context:
        - filters: list of filter configs for template
        - has_active_filters: boolean, True if any filter has value
    """
    filterset_class: Optional[Type[FilterSet]] = None
    
    def get_queryset(self):
        """Apply filters to queryset"""
        queryset = super().get_queryset()
        
        if self.filterset_class:
            self.filterset = self.filterset_class(data=self.request.GET)
            queryset = self.filterset.apply_filters(queryset)
        else:
            self.filterset = None
            
        return queryset
    
    def get_context_data(self, **kwargs):
        """Add filterset to context"""
        context = super().get_context_data(**kwargs)
        
        if self.filterset:
            context['filters'] = self.filterset.to_template_context()
            
            # English: Check if any filter has active value
            has_active = any(
                self.request.GET.get(f['name']) not in [None, '', []]
                for f in context['filters']
            )
            context['has_active_filters'] = has_active
        else:
            context['filters'] = []
            context['has_active_filters'] = False
            
        return context