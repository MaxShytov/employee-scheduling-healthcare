# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

MedShift Scheduler is a Django 5.0 healthcare employee scheduling system designed for medical clinics in Switzerland. It handles shift planning, time tracking, compliance management, and workforce optimization with Swiss-specific features (TARMED billing, KVG/LAMal compliance, FMH certifications).

**Tech Stack:** Django 5.0, Python 3.12, PostgreSQL 15.8, Bootstrap 5.3, Material Design 3, Docker

## Development Commands

### Setup & Running
```bash
# Start PostgreSQL and Redis
docker-compose up -d

# Install dependencies (use venv)
pip install -r requirements/development.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

### Testing
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=apps --cov-report=html

# Run specific app tests
pytest apps/employees/tests/

# Run single test
pytest apps/employees/tests/test_models.py::TestDepartment::test_creation
```

### Database
```bash
# Create migration
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Show migrations
python manage.py showmigrations

# Access database via pgAdmin: http://localhost:15433
# Username: info@trident.software, Password: admin
```

### Code Quality
```bash
# Format code
black .

# Linting
flake8

# Django checks
python manage.py check
```

### Utilities
```bash
# Django shell with extensions
python manage.py shell_plus

# Create app
python manage.py startapp app_name

# Collect static files
python manage.py collectstatic
```

## Architecture

### Project Structure
- **config/** - Django settings split by environment (base.py, development.py, production.py)
- **apps/** - Django applications (modular architecture)
- **templates/** - Global templates with reusable components in templates/core/components/
- **static/** - Static assets (CSS, JS, images)
- **requirements/** - Split requirements files (base.txt, development.txt, production.txt)

### Key Apps
- **accounts** - Custom User model (email-based auth), profile pictures, password reset
- **employees** - Employee, Department, Position, Location, EmployeeDocument models
- **schedules** - Shift scheduling (planned for Phase 1)
- **timeclock** - Time tracking (planned for Phase 1)
- **dashboard** - Main dashboard with analytics
- **core** - Shared utilities, base models, mixins, filters, reusable template components

### Core Architecture Patterns

#### Custom User Model
- Uses email as USERNAME_FIELD instead of username
- Located at apps/accounts/models.py
- Required fields: email, username (legacy), first_name, last_name
- AUTH_USER_MODEL = 'accounts.User' (defined in config/settings/base.py:124)

#### Base Models
All models inherit from `apps.core.models.TimeStampedModel` which provides:
- created_at (auto)
- updated_at (auto)

#### View Architecture
The project uses a mixin-based view architecture with inheritance:

**Base Views:**
- `BaseListView` (apps/core/views/base.py) - Base for all list views with pagination
- All ListView classes should inherit from BaseListView for consistent pagination

**Essential Mixins (apps/core/views/mixins.py):**
- `FilterMixin` - Declarative filtering using FilterSet classes
- `BreadcrumbMixin` - Breadcrumb navigation support
- `ProtectedDeleteMixin` - Prevents deletion when foreign key references exist

**View Pattern:**
```python
class EmployeeListView(
    EmployeeTableMixin,      # App-specific mixin
    FilterMixin,             # Core filtering
    BreadcrumbMixin,         # Breadcrumbs
    LoginRequiredMixin,      # Django auth
    PermissionRequiredMixin, # Django permissions
    BaseListView             # Base (must be last)
):
    model = Employee
    filterset_class = EmployeeFilterSet
    permission_required = 'employees.view_employee'
```

**Mixin Order:** App-specific mixins → Core mixins → Django mixins → BaseListView (last)

#### Filtering System
Custom FilterSet system (apps/core/filters.py) with declarative filters:
- `TextFilter` - Text search with icontains, supports multi-field search via search_fields
- `ChoiceFilter` - Dropdowns from queryset or static choices
- `BooleanFilter` - True/False filters, supports button-style rendering

**Filter Pattern:**
```python
class EmployeeFilterSet(FilterSet):
    search = TextFilter(
        field_name='user__first_name',
        search_fields=['user__first_name', 'user__last_name', 'user__email']
    )
    department = ChoiceFilter(
        field_name='department',
        queryset=Department.objects.filter(is_active=True)
    )
```

#### Caching Pattern
The project uses Redis caching with utility functions:
- `make_key()` - Generate cache keys with namespace
- `make_params_hash()` - Hash request params for cache invalidation
- `get_or_set_stats()` - Cache statistics with TTL
- Cache timeouts defined in CACHE_TIMEOUTS dict in settings

#### Table Rendering System
Custom table rendering with mixins (e.g., EmployeeTableMixin in apps/employees/mixins.py):
- `get_employee_table_columns()` - Define column configuration
- `prepare_employee_table_rows()` - Format data for data_table component
- Supports cell types: avatar, badge, currency, actions
- Used with templates/core/components/data_table.html

#### Template Components
Reusable Material Design 3 components with atomic block-based architecture:

**Layout Components (use these for consistency):**
- **detail_layout.html** ⭐ Universal detail page layout - USE THIS for all detail views
  - Sidebar (left, 4 cols) + Content area (right, 8 cols)
  - Both populated with atomic component blocks
  - Supports tabs in content area
- **page_header.html** - Page headers with action buttons
- **breadcrumbs.html** - Breadcrumb navigation
- **form_container.html** - Form wrapper with Material Design styling

**Atomic Component Blocks (templates/core/components/blocks/):**
These are the building blocks for `detail_layout.html`:
- **avatar_header.html** - Avatar/icon + name + subtitle + badge
- **text_line.html** - Simple text line with styling
- **divider.html** - Horizontal divider
- **field.html** - Icon + label + value (can be link)
- **section_header.html** - Section title + icon + badge

**Data Display Components:**
- **data_table.html** - Tables with sorting, pagination (for list views)
- **stat_card.html** - Dashboard statistics cards
- **empty_state.html** - Empty state messages
- **pagination.html** - Pagination controls

**Interactive Components:**
- **filter_bar.html** - Filter UI rendering
- **confirm_delete.html** - Delete confirmation dialog
- **tabs_navigation.html** - Tab navigation (used within detail_layout)

**Legacy/Deprecated:**
- **profile_card.html** - Use avatar_header block instead
- **info_section.html** - Use section_header + field blocks instead
- **department_card.html** - Not used (was for grid view)

**Component API:**

**breadcrumbs.html:**
```python
[{'label': str, 'url': str|None}]
```

**page_header.html actions:**
```python
[{'label': str, 'icon': str, 'href': str, 'style': str}]
```

**detail_layout.html (NEW BLOCK SYSTEM):**
```python
sidebar_blocks = [
    {'type': 'avatar_header', 'icon': 'business', 'name': str, 'subtitle': str, 'badge': dict},
    {'type': 'divider'},
    {'type': 'section_header', 'icon': str, 'title': str, 'badge': dict},
    {'type': 'field', 'icon': str, 'label': str, 'value': str, 'link': str},
    {'type': 'fields_group', 'fields': [field_dicts]},
]

content_blocks = [
    {'type': 'table', 'title': str, 'icon': str, 'columns': [...], 'rows': [...], 'empty_message': str},
    {'type': 'section_header', 'icon': str, 'title': str},
    {'type': 'fields_group', 'fields': [...]},
    {'type': 'divider'},
]

# With tabs:
tabs = [{'id': str, 'label': str, 'icon': str, 'active': bool}]
content_blocks = [...] # each block can have 'tab': 'tab_id' to show only in that tab
```

Note: Use `'label'` for text in breadcrumbs/actions for consistency.

### Model Relationships
- User (1) → (0..1) Employee - OneToOne relationship via employee_profile
- Employee (N) → (1) Department - ForeignKey with PROTECT
- Employee (N) → (1) Position - ForeignKey with PROTECT
- Employee (N) → (1) Location - ForeignKey with PROTECT
- Employee (1) → (N) EmployeeDocument - ForeignKey with CASCADE
- Department/Location (N) → (0..1) User - Manager relationship (SET_NULL)

### URL Structure
- / → Redirects to /accounts/login/
- /admin/ → Django admin
- /accounts/ → Login, logout, password reset
- /dashboard/ → Main dashboard
- /employees/ → Employee management (CRUD)
- /help/ → Help documentation

### Settings Architecture
Split settings pattern:
- **base.py** - Common settings for all environments
- **development.py** - Debug toolbar, console email backend, relaxed validators
- **production.py** - Production-specific settings (not shown)
- Environment controlled via DJANGO_SETTINGS_MODULE (default: config.settings.development)

Key settings:
- TIME_ZONE = 'Europe/Zurich'
- AUTH_USER_MODEL = 'accounts.User'
- Pagination defaults in PAGINATION_DEFAULTS dict
- Cache configuration with CACHE_TIMEOUTS and CACHE_NS

## Swiss Healthcare Specific

- Time zone: Europe/Zurich
- Currency: Swiss Francs (CHF)
- Cantonal system support (SWISS_CANTON setting)
- FMH medical certifications tracking
- TARMED billing code integration (planned)
- KVG/LAMal compliance requirements

## Development Guidelines

### When Creating New Views

**List Views:**
1. Inherit from BaseListView for list views (provides consistent pagination)
2. Use FilterMixin + FilterSet for filtering instead of manual query params
3. Add BreadcrumbMixin and implement get_breadcrumbs()
4. Add permission_required for all views
5. Use select_related()/prefetch_related() in get_queryset() to optimize queries

**Detail Views (NEW BLOCK SYSTEM):**
1. Use **detail_layout.html** with atomic component blocks
2. Build `sidebar_blocks` list with block dicts (avatar_header, section_header, field, divider, etc.)
3. Build `content_blocks` list for main content area (table, fields_group, section_header, etc.)
4. For tabs: add `tabs` config and set `'tab': 'tab_id'` on content blocks
5. Add BreadcrumbMixin and implement get_breadcrumbs()
6. Add permission_required for all views
7. See DepartmentDetailView in [views.py:1147-1213](apps/employees/views.py#L1147-L1213) for example

Example block structure:
```python
sidebar_blocks = [
    {'type': 'avatar_header', 'icon': 'business', 'name': dept.name, 'badge': status_badge},
    {'type': 'divider'},
    {'type': 'section_header', 'icon': 'info', 'title': _('Basic Information')},
    {'type': 'field', 'icon': 'person', 'label': _('Manager'), 'value': manager_name},
]
```

**Form Views (Create/Update):**
1. **IMPORTANT:** For models with `is_active` field, always use Active/Inactive toggle buttons
2. Implement `get_form_sections()` to return structured form data
3. Place toggle buttons next to the main identifier field (e.g., code, employee_id)
4. Use `has_toggle: True` and `toggle_field: form['is_active']` in field config
5. Templates must check `field_data.has_toggle` and use appropriate component

**Active/Inactive Toggle Pattern (REQUIRED for models with is_active field):**
```python
def get_form_sections(self, form):
    return [
        {
            'title': _('Basic Information'),
            'icon': 'info',
            'fields': [
                {'field': form['name'], 'col_class': 'col-md-6'},
                {
                    'field': form['code'],  # Main identifier field
                    'col_class': 'col-md-6',
                    'has_toggle': True,  # Enable toggle buttons
                    'toggle_field': form['is_active'],  # Link to is_active field
                },
                {'field': form['description'], 'col_class': 'col-12'},
            ]
        }
    ]
```

Template pattern (see department_form.html or position_form.html):
```django
{% for field_data in section.fields %}
    {% if field_data.has_toggle %}
        {# Field with Active/Inactive toggle buttons #}
        {% include "core/components/form_field_with_toggle.html" with field=field_data.field toggle_field=field_data.toggle_field col_class=field_data.col_class|default:'col-md-6' %}
    {% else %}
        {# Regular form field #}
        {% include "core/components/form_field.html" with field=field_data.field col_class=field_data.col_class|default:'col-md-6' %}
    {% endif %}
{% endfor %}
```

**Why:** This provides consistent UX across all forms and makes status changes more visible than a checkbox. Toggle buttons are placed next to the identifier field (code/ID) for quick visual reference.

**Delete Views with Protection (REQUIRED for models with on_delete=PROTECT):**
1. **Always implement get_blocking_references()** for models that have ForeignKey relationships with on_delete=PROTECT
2. Check for active related objects (e.g., employees assigned to a position/department)
3. Return list of dicts with 'type', 'count', 'message' keys for each blocking issue
4. Template must handle two states:
   - `has_blocking_refs=True`: Show warning card (yellow bg-warning) with blocking issues list
   - `has_blocking_refs=False`: Show confirm_delete.html component for normal deletion
5. Override post() to check blocking_refs and redirect with error message if blocked

Example implementation (see DepartmentDeleteView or PositionDeleteView):
```python
def get_blocking_references(self):
    """Check for blocking references."""
    blocking = []

    # Check for active employees
    active_count = self.object.employees.filter(is_active=True).count()
    if active_count > 0:
        blocking.append({
            'type': 'active_employees',
            'count': active_count,
            'message': _('%(count)d active employee(s) assigned') % {'count': active_count}
        })

    return blocking

def get_context_data(self, **kwargs):
    ctx = super().get_context_data(**kwargs)
    blocking_refs = self.get_blocking_references()
    ctx['has_blocking_refs'] = len(blocking_refs) > 0
    ctx['blocking_refs'] = blocking_refs
    ctx['cancel_url'] = reverse('app:detail', kwargs={'pk': self.object.pk})

    if ctx['has_blocking_refs']:
        ctx['blocking_message'] = _('Cannot delete. Resolve issues first.')

    return ctx

def post(self, request, *args, **kwargs):
    self.object = self.get_object()
    blocking_refs = self.get_blocking_references()

    if blocking_refs:
        messages_list = [ref['message'] for ref in blocking_refs]
        messages.error(request, _('Cannot delete: ') + '; '.join(messages_list))
        return redirect('app:detail', pk=self.object.pk)

    return super().post(request, *args, **kwargs)
```

Template pattern (see department_confirm_delete.html or position_confirm_delete.html):
```django
{% if has_blocking_refs %}
    {# Yellow warning card with blocking issues list #}
    <div class="card border-warning shadow-sm">
        <div class="card-header bg-warning text-dark">
            <h5 class="mb-0">
                <span class="material-icons">warning</span>
                {% trans "Cannot Delete Object" %}
            </h5>
        </div>
        <div class="card-body">
            <p>{{ blocking_message }}</p>
            <div class="alert alert-danger">
                <h6>{% trans "Blocking Issues" %}</h6>
                <ul>
                    {% for ref in blocking_refs %}
                        <li>{{ ref.message }}</li>
                    {% endfor %}
                </ul>
            </div>
            <a href="{{ cancel_url }}" class="btn btn-primary">
                {% trans "Back" %}
            </a>
        </div>
    </div>
{% else %}
    {# Normal delete confirmation #}
    {% include "core/components/confirm_delete.html" with cancel_url=cancel_url confirm_text="Delete Object" %}
{% endif %}
```

**Other Delete Views:**
1. Use confirm_delete.html component for simple deletions (warns about permanent deletion)
2. Add BreadcrumbMixin and implement get_breadcrumbs()
3. For soft delete, override form_valid() to set is_active=False instead of deleting

### When Creating New Models
1. Inherit from TimeStampedModel (provides created_at/updated_at)
2. Add verbose_name and verbose_name_plural in Meta
3. Add ordering in Meta
4. Add database indexes for frequently filtered/joined fields
5. Implement __str__() method
6. Use settings.AUTH_USER_MODEL for ForeignKey to User (not direct import)
7. Add get_absolute_url() for detail views
8. If model has `is_active` field, ensure forms use Active/Inactive toggle buttons (see "Form Views" section above)

### When Creating New Filters
1. Create FilterSet subclass in app's filters.py
2. Use TextFilter with search_fields for multi-field search
3. Use ChoiceFilter with queryset for ForeignKey filters
4. Add filterset_class to view
5. Filters automatically render via filter_bar.html component

### When Creating Templates

**CRITICAL RULE: Templates should contain MINIMAL HTML code. Use components for all HTML structures.**

**General Principles:**
1. Extend from base template (`layouts/dashboard_layout.html`)
2. **DO NOT write HTML structures** - use reusable components from `templates/core/components/`
3. Templates should only contain component includes with parameters
4. All HTML structures, styling, and layout should be in components
5. Follow Material Design 3 patterns (implemented in components)
6. Pass structured data dicts from views to components
7. **DO NOT include breadcrumbs** - automatically included in `dashboard_layout.html` for all views with `BreadcrumbMixin`
8. **DO NOT include page_header** - automatically included in `dashboard_layout.html` when `page_title` or `title` is in context

**Template Types and Required Structure:**

**Detail Views (STRICT - NO HTML):**
Must use component-only structure. See `department_detail.html` or `position_detail.html`:
```django
{% extends "layouts/dashboard_layout.html" %}
{% load static i18n %}

{% block dashboard_content %}
{# Breadcrumbs and Page Header are auto-included via dashboard_layout.html #}

{# Detail Layout #}
{% include "core/components/detail_layout.html" with sidebar_blocks=sidebar_blocks content_blocks=content_blocks ... %}
{% endblock %}
```

**Form Views (STRICT - NO HTML):**
Must use `form_container.html` component. See `employee_form.html`, `department_form.html`, `position_form.html`:
```django
{% extends "layouts/dashboard_layout.html" %}
{% load static i18n %}

{% block dashboard_content %}
{# Breadcrumbs and Page Header are auto-included via dashboard_layout.html #}

{# Form Container - all HTML is in component #}
<div class="row justify-content-center">
    <div class="col-lg-10">
        {% include "core/components/form_container.html" with forms=forms sections=form_sections cancel_url=cancel_url submit_text=submit_text %}
    </div>
</div>
{% endblock %}
```

**Delete Confirmation Views (STRICT - NO HTML):**
Must use `confirm_delete.html` component. See `department_confirm_delete.html`, `position_confirm_delete.html`:
```django
{% extends "layouts/dashboard_layout.html" %}
{% load static i18n %}

{% block dashboard_content %}
{# Breadcrumbs and Page Header are auto-included via dashboard_layout.html #}

{# Delete Confirmation #}
{% include "core/components/confirm_delete.html" with has_blocking_refs=has_blocking_refs blocking_refs=blocking_refs blocking_message=blocking_message blocking_title=_("Cannot Delete") cancel_url=cancel_url cancel_text=_("Back") confirm_text=_("Delete") %}
{% endblock %}
```

**List Views:**
Use table/filter components with minimal wrapper HTML:
```django
{% extends "layouts/dashboard_layout.html" %}

{% block dashboard_content %}
{# Breadcrumbs and Page Header are auto-included via dashboard_layout.html #}

{# Statistics Cards #}
{% if stats_cards %}
    {% include "core/components/stats_row.html" with stats_cards=stats_cards %}
{% endif %}

{# Filters #}
{% include "core/components/filter_bar.html" with filters=filters action_url=action_url %}

{# Data Table #}
{% include "core/components/data_table.html" with columns=table_columns rows=table_rows %}

{# Pagination #}
{% include "core/components/pagination.html" with page_obj=page_obj %}
{% endblock %}
```

**When HTML is Allowed:**
- Simple wrapper divs for layout (e.g., `<div class="row justify-content-center">`)
- These should be candidates for future componentization
- If you need more than 3 lines of HTML, create a component instead

**Bad Example (DO NOT DO THIS):**
```django
{# DON'T write HTML structures in templates #}
<div class="card border-0 shadow-sm">
    <div class="card-header bg-white">
        <h5>{{ title }}</h5>
    </div>
    <div class="card-body">
        <form method="post">
            {# ... form fields ... #}
        </form>
    </div>
</div>
```

**Good Example:**
```django
{# DO use components #}
{% include "core/components/form_container.html" with forms=forms sections=form_sections %}
```

### Database Migrations
- Always run makemigrations after model changes
- Review generated migrations before applying
- Never edit migrations after they've been committed and shared
- Use data migrations for complex data transformations

### Foreign Key Patterns
- Use PROTECT for critical relationships (Department, Position, Location)
  - **IMPORTANT:** When using PROTECT, you MUST implement get_blocking_references() in DeleteView
  - See "Delete Views with Protection" section above for required implementation
- Use CASCADE for dependent objects (EmployeeDocument)
- Use SET_NULL for optional relationships (managers)
- Always add related_name for reverse lookups

### Form Patterns
- Use crispy_forms with Bootstrap 5 template pack
- Leverage widget_tweaks for form customization
- Validate Swiss phone numbers with validate_swiss_phone
- Handle profile picture uploads via FileField with upload_to pattern

## Docker & Deployment

### Development Docker
```bash
# Start services
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

Services:
- PostgreSQL: localhost:15432
- Redis: localhost:16379
- pgAdmin: http://localhost:15433

### Production
Uses Docker Swarm (see docker-compose-swarm.yaml) with:
- Traefik for load balancing and SSL
- Secrets management for sensitive data
- Nginx reverse proxy
