# apps/core/views/mixins.py
from typing import Optional, Type, List, Dict, Any
from django.db import models
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.shortcuts import redirect
from apps.core.filters import FilterSet


class FilterMixin:
    """Mixin for ListView to add declarative filtering."""
    
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
        context['action_url'] = self.request.path

        return context


class BreadcrumbMixin:
    """
    Mixin to add breadcrumbs to context.
    
    Usage:
        class MyView(BreadcrumbMixin, ListView):
            breadcrumb_base = [
                {'label': _('Home'), 'url': 'core:home'},
                {'label': _('Employees'), 'url': 'employees:employee_list'},
            ]
    """
    breadcrumb_base: List[Dict[str, Any]] = []
    
    def get_breadcrumb_base(self):
        """Override to customize base breadcrumbs"""
        return self.breadcrumb_base
    
    def get_breadcrumbs(self):
        """Override to add dynamic breadcrumbs"""
        return self.get_breadcrumb_base()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['breadcrumb_items'] = self.get_breadcrumbs()
        return context


class ProtectedDeleteMixin:
    """
    Mixin for DeleteView to check for blocking references before deletion.
    
    Usage:
        class DepartmentDeleteView(ProtectedDeleteMixin, DeleteView):
            def get_blocking_references(self):
                emp_count = self.object.employees.filter(is_active=True).count()
                if emp_count > 0:
                    return [_('%(count)d active employee(s)') % {'count': emp_count}]
                return []
    """
    
    def get_blocking_references(self) -> List[str]:
        """
        Override this method to return list of blocking references.
        Return empty list if deletion is allowed.
        """
        return []
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        blocking_refs = self.get_blocking_references()
        
        context['blocking_refs'] = blocking_refs
        context['can_delete'] = len(blocking_refs) == 0
        
        return context
    
    def post(self, request, *args, **kwargs):
        """Check for blocking references before deletion"""
        self.object = self.get_object()
        blocking_refs = self.get_blocking_references()
        
        if blocking_refs:
            messages.error(
                request,
                _('Cannot delete: ') + '; '.join(blocking_refs)
            )
            return redirect(self.get_success_url())
        
        messages.success(request, _('Deleted successfully.'))
        return super().post(request, *args, **kwargs)