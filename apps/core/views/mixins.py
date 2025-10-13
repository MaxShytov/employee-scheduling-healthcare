# apps/core/views/mixins.py
from typing import Optional, Type
from django.db import models
from apps.core.filters import FilterSet


class FilterMixin:
    """
    Mixin for ListView to add declarative filtering.
    
    Usage in view:
        class EmployeeListView(FilterMixin, ListView):
            model = Employee
            filterset_class = EmployeeFilterSet
            paginate_by = 25
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
            context['has_active_filters'] = self.filterset.is_active
        else:
            context['filters'] = []
            context['has_active_filters'] = False
            
        return context