"""
Reusable UI components for templates.
Provides consistent styling across the entire application.
"""

from django import template
from django.utils.safestring import mark_safe
from django.utils.html import format_html

register = template.Library()


# ============================================
# BUTTONS
# ============================================

@register.inclusion_tag('core/components/action_buttons.html')
def action_buttons(obj=None, view_url=None, edit_url=None, delete_url=None, custom_buttons=None):
    """
    Render standard action buttons for list views.
    
    Usage:
        {% action_buttons obj=location %}
        {% action_buttons view_url=url edit_url=url %}
    """
    # If object is provided, try to get URLs from it
    if obj:
        view_url = view_url or getattr(obj, 'get_absolute_url', lambda: None)()
        edit_url = edit_url or getattr(obj, 'get_edit_url', lambda: None)()
        delete_url = delete_url or getattr(obj, 'get_delete_url', lambda: None)()
    
    return {
        'view_url': view_url,
        'edit_url': edit_url,
        'delete_url': delete_url,
        'custom_buttons': custom_buttons or [],
    }


@register.simple_tag
def button(text, url='#', color='primary', size='sm', icon=None, outline=True):
    """
    Render a styled button.
    
    Usage:
        {% button 'Add Location' url=url color='primary' icon='add' %}
    """
    btn_class = f"btn-outline-{color}" if outline else f"btn-{color}"
    size_class = f"btn-{size}" if size else ""
    
    icon_html = ''
    if icon:
        icon_html = f'<span class="material-icons" style="font-size: 16px; vertical-align: middle;">{icon}</span> '
    
    return format_html(
        '<a href="{}" class="btn {} {}">{}{}</a>',
        url, btn_class, size_class, mark_safe(icon_html), text
    )


# ============================================
# ICONS
# ============================================

@register.simple_tag
def icon(name, size=16, color=''):
    """
    Render Material Icon.
    
    Usage:
        {% icon 'edit' %}
        {% icon 'delete' size=20 color='text-danger' %}
    """
    return format_html(
        '<span class="material-icons {}" style="font-size: {}px; vertical-align: middle;">{}</span>',
        color, size, name
    )


# ============================================
# BADGES
# ============================================

@register.simple_tag
def badge(text, color='primary', pill=False, icon=None):
    """
    Render Bootstrap badge.
    
    Usage:
        {% badge 'Active' color='success' %}
        {% badge '5' color='primary' pill=True %}
    """
    pill_class = 'rounded-pill' if pill else ''
    icon_html = ''
    
    if icon:
        icon_html = f'<span class="material-icons" style="font-size: 14px; vertical-align: middle;">{icon}</span> '
    
    return format_html(
        '<span class="badge bg-{} {}">{}{}</span>',
        color, pill_class, mark_safe(icon_html), text
    )


@register.simple_tag
def status_badge(is_active):
    """
    Render Active/Inactive status badge.
    
    Usage:
        {% status_badge object.is_active %}
    """
    if is_active:
        return badge('Active', color='success')
    return badge('Inactive', color='secondary')


# ============================================
# CARDS
# ============================================

@register.inclusion_tag('core/components/stat_card.html')
def stat_card(title, value, icon, color='primary', url=None):
    """
    Render statistics card.
    
    Usage:
        {% stat_card title='Total Employees' value=50 icon='people' color='primary' %}
    """
    return {
        'title': title,
        'value': value,
        'icon': icon,
        'color': color,
        'url': url,
    }


# ============================================
# TABLES
# ============================================

@register.simple_tag
def table_header(text, sortable=False, sort_field=None, current_sort=None):
    """
    Render table header with optional sorting.
    
    Usage:
        {% table_header 'Name' sortable=True sort_field='name' %}
    """
    if sortable and sort_field:
        # Add sort icons logic here
        sort_icon = ''
        if current_sort == sort_field:
            sort_icon = '↑'
        elif current_sort == f'-{sort_field}':
            sort_icon = '↓'
        
        return format_html(
            '<th class="sortable">{} {}</th>',
            text, sort_icon
        )
    
    return format_html('<th>{}</th>', text)


# ============================================
# PAGINATION
# ============================================

@register.inclusion_tag('core/components/pagination.html')
def pagination(page_obj, url_name=None):
    """
    Render pagination controls.
    
    Usage:
        {% pagination page_obj %}
    """
    return {
        'page_obj': page_obj,
        'url_name': url_name,
    }


# ============================================
# FILTERS
# ============================================

@register.inclusion_tag('core/components/search_filters.html')
def search_filters(form, show_search=True):
    """
    Render search and filter form.
    
    Usage:
        {% search_filters search_form %}
    """
    return {
        'form': form,
        'show_search': show_search,
    }


# ============================================
# BREADCRUMBS
# ============================================

@register.inclusion_tag('core/components/breadcrumbs.html')
def breadcrumbs(items):
    """
    Render breadcrumb navigation.

    Usage:
        {% breadcrumbs items %}
        where items = [
            {'label': 'Home', 'url': '/'},
            {'label': 'Employees', 'url': '/employees/'},
            {'label': 'John Doe'},  # Last item (active)
        ]
    """
    return {'items': items}


# ============================================
# ALERTS
# ============================================

@register.simple_tag
def alert(message, alert_type='info', dismissible=True):
    """
    Render Bootstrap alert.
    
    Usage:
        {% alert 'Success!' alert_type='success' %}
    """
    dismiss_btn = ''
    if dismissible:
        dismiss_btn = '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>'
    
    return format_html(
        '<div class="alert alert-{} {}" role="alert">{}{}</div>',
        alert_type,
        'alert-dismissible fade show' if dismissible else '',
        message,
        mark_safe(dismiss_btn)
    )


# ============================================
# EMPTY STATES
# ============================================

@register.inclusion_tag('core/components/empty_state.html')
def empty_state(icon, title, message, button_text=None, button_url=None):
    """
    Render empty state placeholder.
    
    Usage:
        {% empty_state icon='inbox' title='No items found' message='Try adjusting filters' %}
    """
    return {
        'icon': icon,
        'title': title,
        'message': message,
        'button_text': button_text,
        'button_url': button_url,
    }


# ============================================
# FORMS
# ============================================

@register.inclusion_tag('core/components/form_field.html')
def form_field(field, col_class='col-12'):
    """
    Render a form field with label, help text, and errors.
    
    Usage:
        {% form_field form.name col_class='col-md-6' %}
    """
    return {
        'field': field,
        'col_class': col_class,
    }


# ============================================
# LOADING SPINNER
# ============================================

@register.simple_tag
def spinner(size='md', color='primary'):
    """
    Render loading spinner.
    
    Usage:
        {% spinner %}
        {% spinner size='lg' color='danger' %}
    """
    size_class = f'spinner-border-{size}' if size != 'md' else ''
    
    return format_html(
        '<div class="spinner-border text-{} {}" role="status"><span class="visually-hidden">Loading...</span></div>',
        color, size_class
    )