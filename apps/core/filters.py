# apps/core/filters.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from typing import Any, Optional
from django.db.models import Q


class BaseFilter:
    """Base class for all filters."""
    
    def __init__(
        self,
        field_name: str,
        label: str,
        lookup: str = 'exact',
        required: bool = False,
        initial: Any = None,
        help_text: str = '',
    ):
        self.field_name = field_name
        self.label = label
        self.lookup = lookup
        self.required = required
        self.initial = initial
        self.help_text = help_text
        self.value = None
        self.filter_name = None  # ← Новое: уникальное имя для HTML формы

    def get_filter_kwargs(self) -> dict:
        """Returns Q object kwargs for queryset filtering"""
        if self.value is None or self.value == '':
            return {}
        lookup_key = f"{self.field_name}__{self.lookup}"
        return {lookup_key: self.value}

    def bind(self, value: Any):
        """Bind value from request.GET"""
        self.value = self.clean(value)
        return self

    def clean(self, value: Any) -> Any:
        """Override in subclasses for value validation/transformation"""
        return value

    def to_template_context(self) -> dict:
        """Returns dict for template rendering"""
        raise NotImplementedError
    

class TextFilter(BaseFilter):
    """Filter for text search (icontains by default)"""
    
    def __init__(self, field_name: str, label: str, lookup: str = 'icontains', **kwargs):
        # Extract TextFilter-specific kwargs before passing to parent
        self.placeholder = kwargs.pop('placeholder', '')
        self.search_fields = kwargs.pop('search_fields', None)  # ← Новое: список полей для поиска
        # Now pass remaining kwargs to parent
        super().__init__(field_name, label, lookup, **kwargs)

    def get_filter_kwargs(self) -> dict:
        """Returns Q object kwargs for queryset filtering"""
        if self.value is None or self.value == '':
            return {}
        
        # If multiple search fields specified, use Q objects
        if self.search_fields:
            q_objects = Q()
            for field in self.search_fields:
                lookup_key = f"{field}__{self.lookup}"
                q_objects |= Q(**{lookup_key: self.value})
            return {'__q': q_objects}  # Special marker for Q object
        
        # Single field search
        lookup_key = f"{self.field_name}__{self.lookup}"
        return {lookup_key: self.value}

    def to_template_context(self) -> dict:
        return {
            'type': 'text',
            'name': self.filter_name or self.field_name,
            'label': self.label,
            'value': self.value or '',
            'placeholder': self.placeholder,
            'help_text': self.help_text,
        }



class ChoiceFilter(BaseFilter):
    """Filter for select/dropdown"""
    
    def __init__(
        self,
        field_name: str,
        label: str,
        choices: list[tuple] = None,
        queryset: Optional[models.QuerySet] = None,
        empty_label: str = '---------',
        **kwargs
    ):
        # Extract ChoiceFilter-specific params (already in signature, not in kwargs)
        self._choices = choices
        self._queryset = queryset
        self.empty_label = empty_label
        # Pass remaining kwargs to parent
        super().__init__(field_name, label, **kwargs)

    def get_choices(self) -> list[dict]:
        """
        Returns choices as list of dicts for template.
        
        Supports both static choices and dynamic queryset.
        """
        options = []
        if self.empty_label:
            options.append({'value': '', 'label': self.empty_label})
        
        if self._queryset is not None:
            # Dynamic choices from queryset
            for obj in self._queryset:
                options.append({
                    'value': str(obj.pk),
                    'label': str(obj),
                })
        elif self._choices:
            # Static choices (like Django choices)
            for value, label in self._choices:
                options.append({'value': str(value), 'label': str(label)})
        
        return options

    def clean(self, value: Any) -> Any:
        if value == '' or value is None:
            return None
        # If queryset - validate that ID exists
        if self._queryset is not None:
            try:
                return int(value)
            except (ValueError, TypeError):
                return None
        return value

    def to_template_context(self) -> dict:
        return {
            'type': 'select',  # ← ОБЯЗАТЕЛЬНО должно быть 'select'!
            'name': self.filter_name or self.field_name,
            'label': self.label,
            'value': str(self.value) if self.value else '',
            'options': self.get_choices(),
            'help_text': self.help_text,
        }


class BooleanFilter(BaseFilter):
    """Filter for boolean/checkbox"""

    def __init__(
        self,
        field_name: str,
        label: str,
        as_buttons: bool = False,
        true_label: str = None,
        false_label: str = None,
        true_color: str = 'success',
        false_color: str = 'danger',
        **kwargs
    ):
        self.as_buttons = as_buttons
        self.true_label = true_label or _('Active')
        self.false_label = false_label or _('Inactive')
        self.true_color = true_color
        self.false_color = false_color
        super().__init__(field_name, label, lookup='exact', **kwargs)

    def clean(self, value: Any) -> Optional[bool]:
        if value in ('true', 'True', '1', 1, True):
            return True
        elif value in ('false', 'False', '0', 0, False):
            return False
        return None  # None означает "показать всех"

    def get_filter_kwargs(self) -> dict:
        if self.value is None:
            return {}  # Не фильтруем - показываем всех
        return {self.field_name: self.value}

    def to_template_context(self) -> dict:
        if self.as_buttons:
            # Render as button group
            return {
                'type': 'toggle_buttons',
                'name': self.filter_name or self.field_name,
                'label': self.label,
                'value': self.value,  # None / True / False
                'true_label': self.true_label,
                'false_label': self.false_label,
                'true_color': self.true_color,
                'false_color': self.false_color,
                'help_text': self.help_text,
            }
        else:
            # Render as checkbox
            return {
                'type': 'checkbox',
                'name': self.filter_name or self.field_name,
                'label': self.label,
                'checked': self.value is True,
                'help_text': self.help_text,
            }

class DateFilter(BaseFilter):
    """Filter for date inputs"""
    
    def __init__(self, field_name: str, label: str, lookup: str = 'exact', **kwargs):
        # DateFilter doesn't have extra params
        super().__init__(field_name, label, lookup, **kwargs)

    def clean(self, value: Any) -> Any:
        from django.utils.dateparse import parse_date
        if isinstance(value, str):
            return parse_date(value)
        return value

    def to_template_context(self) -> dict:
        return {
            'type': 'date',
            'name': self.filter_name or self.field_name,  # ← Используем filter_name
            'label': self.label,
            'value': self.value.isoformat() if self.value else '',
            'help_text': self.help_text,
        }


class NumberFilter(BaseFilter):
    """Filter for numeric inputs"""
    
    def __init__(self, field_name: str, label: str, lookup: str = 'exact', **kwargs):
        # Extract NumberFilter-specific kwargs
        self.min_value = kwargs.pop('min_value', None)
        self.max_value = kwargs.pop('max_value', None)
        # Pass remaining kwargs to parent
        super().__init__(field_name, label, lookup, **kwargs)

    def clean(self, value: Any) -> Any:
        try:
            return float(value) if value else None
        except (ValueError, TypeError):
            return None

    def to_template_context(self) -> dict:
        context = {
            'type': 'number',
            'name': self.filter_name or self.field_name,
            'label': self.label,
            'value': self.value or '',
            'help_text': self.help_text,
        }
        if self.min_value is not None:
            context['min'] = self.min_value
        if self.max_value is not None:
            context['max'] = self.max_value
        return context


class FilterSet:
    """Container for filters with declarative syntax."""
    
    def __init__(self, data: dict = None):
        self.data = data or {}
        self.filters = self._collect_filters()
        self._bind_data()

    def _collect_filters(self) -> dict[str, BaseFilter]:
        """
        Collect all filter instances from class attributes.
        
        Preserves declaration order using __dict__.
        """
        filters = {}
        
        # English: Iterate through class __dict__ to preserve declaration order (Python 3.7+)
        for name, attr in self.__class__.__dict__.items():
            if name.startswith('_'):
                continue
            if isinstance(attr, BaseFilter):
                # Create instance copy for this FilterSet instance
                filter_copy = self._copy_filter(attr)
                filter_copy.filter_name = name  # ← Устанавливаем уникальное имя
                filters[name] = filter_copy
        
        return filters

    def _copy_filter(self, filter_obj: BaseFilter) -> BaseFilter:
        """Create a copy of filter with all its attributes"""
        # Get the filter class
        filter_class = type(filter_obj)
        
        # Base kwargs WITHOUT lookup (we'll pass it explicitly)
        base_kwargs = {
            'required': filter_obj.required,
            'initial': filter_obj.initial,
            'help_text': filter_obj.help_text,
        }
        
        # Add type-specific attributes and create instance
        if isinstance(filter_obj, TextFilter):
            return filter_class(
                filter_obj.field_name,
                filter_obj.label,
                lookup=filter_obj.lookup,
                placeholder=filter_obj.placeholder,
                search_fields=filter_obj.search_fields,  # ← Копируем search_fields
                **base_kwargs
            )
                
        elif isinstance(filter_obj, ChoiceFilter):
            return filter_class(
                filter_obj.field_name,
                filter_obj.label,
                choices=filter_obj._choices,
                queryset=filter_obj._queryset,
                empty_label=filter_obj.empty_label,
                lookup=filter_obj.lookup,  # Explicit
                **base_kwargs
            )
        
        elif isinstance(filter_obj, NumberFilter):
            return filter_class(
                filter_obj.field_name,
                filter_obj.label,
                lookup=filter_obj.lookup,  # Explicit
                min_value=filter_obj.min_value,
                max_value=filter_obj.max_value,
                **base_kwargs
            )
        
        elif isinstance(filter_obj, DateFilter):
            return filter_class(
                filter_obj.field_name,
                filter_obj.label,
                lookup=filter_obj.lookup,  # Explicit
                **base_kwargs
            )
        
        elif isinstance(filter_obj, BooleanFilter):
            return filter_class(
                filter_obj.field_name,
                filter_obj.label,
                as_buttons=filter_obj.as_buttons,
                true_label=filter_obj.true_label,
                false_label=filter_obj.false_label,
                true_color=filter_obj.true_color,
                false_color=filter_obj.false_color,
                **base_kwargs
            )
        
        else:
            # Fallback for custom filter types
            return filter_class(
                filter_obj.field_name,
                filter_obj.label,
                lookup=filter_obj.lookup,
                **base_kwargs
            )

    def _bind_data(self):
        """Bind request.GET data to filters"""
        for name, filter_obj in self.filters.items():
            # English: Use filter_name (unique) instead of field_name for GET params
            value = self.data.get(filter_obj.filter_name or filter_obj.field_name)
            if value:
                filter_obj.bind(value)

    def apply_filters(self, queryset):
        """Apply all active filters to queryset"""
        for filter_obj in self.filters.values():
            filter_kwargs = filter_obj.get_filter_kwargs()
            if filter_kwargs:
                # Check for Q object (special key '__q')
                if '__q' in filter_kwargs:
                    queryset = queryset.filter(filter_kwargs['__q'])
                else:
                    queryset = queryset.filter(**filter_kwargs)
        return queryset

    def to_template_context(self) -> list[dict]:
        """Returns list of filter dicts for template"""
        return [
            f.to_template_context()
            for f in self.filters.values()
        ]

    @property
    def is_active(self) -> bool:
        """Check if any filter has value"""
        return any(f.value for f in self.filters.values())