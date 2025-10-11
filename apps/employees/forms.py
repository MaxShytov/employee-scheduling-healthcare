"""
Forms for employee management.
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

from apps.accounts.models import User
from .models import Department, Location, Position, Employee, EmployeeDocument


class DepartmentForm(forms.ModelForm):
    """Form for creating/editing departments."""
    
    class Meta:
        model = Department
        fields = ('name', 'code', 'description', 'manager', 'is_active')
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Department name')
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Department code (e.g., URG, CHIR)')
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Department description')
            }),
            'manager': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }


class PositionForm(forms.ModelForm):
    """Form for creating/editing positions."""
    
    class Meta:
        model = Position
        fields = (
            'title', 'code', 'description', 
            'requires_certification',
            'min_hourly_rate', 'max_hourly_rate',
            'is_active'
        )
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Position title')
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Position code (e.g., RN, MD)')
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Position description')
            }),
            'requires_certification': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'min_hourly_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': _('Minimum hourly rate (CHF)'),
                'step': '0.01'
            }),
            'max_hourly_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': _('Maximum hourly rate (CHF)'),
                'step': '0.01'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        min_rate = cleaned_data.get('min_hourly_rate')
        max_rate = cleaned_data.get('max_hourly_rate')
        
        if min_rate and max_rate and min_rate > max_rate:
            raise ValidationError({
                'max_hourly_rate': _('Maximum rate must be greater than minimum rate')
            })
        
        return cleaned_data


class EmployeeUserForm(forms.ModelForm):
    """Form for employee user information."""
    
    class Meta:
        model = User
        fields = (
            'first_name', 'last_name', 'email',
            'phone', 'country', 'date_of_birth',
            'profile_picture'  # ← Добавить
        )
        widgets = {
            'first_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('First name')
            }),
            'last_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Last name')
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': _('Email address')
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('+41 XX XXX XX XX')
            }),
            'country': forms.Select(attrs={
                'class': 'form-select'
            }),
            'date_of_birth': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'profile_picture': forms.FileInput(attrs={  # ← Добавить
                'class': 'form-control'
            }),
        }

class EmployeeForm(forms.ModelForm):
    """Form for employee employment information."""
            
    class Meta:
        model = Employee
        fields = (
            'employee_id', 'department', 'position', 'location',  # ← Добавьте location
            'employment_type', 'hire_date', 'termination_date',
            'hourly_rate', 'weekly_hours',
            'emergency_contact_name', 'emergency_contact_phone',
            'emergency_contact_relationship',
            'notes', 'is_active'
        )
        widgets = {
            'employee_id': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Employee ID (e.g., EMP1001)')
            }),
            'department': forms.Select(attrs={
                'class': 'form-select'
            }),
            'position': forms.Select(attrs={
                'class': 'form-select'
            }),
            'location': forms.Select(attrs={  # ← Добавьте widget для location
                'class': 'form-select'
            }),
            'employment_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'hire_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'termination_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'hourly_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': _('Hourly rate (CHF)'),
                'step': '0.01'
            }),
            'weekly_hours': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': _('Weekly hours'),
                'step': '0.5'
            }),
            'emergency_contact_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Emergency contact name')
            }),
            'emergency_contact_phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('+41 XX XXX XX XX')
            }),
            'emergency_contact_relationship': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Relationship (spouse, parent, etc.)')
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Internal notes')
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        hire_date = cleaned_data.get('hire_date')
        termination_date = cleaned_data.get('termination_date')
        
        if hire_date and termination_date and termination_date < hire_date:
            raise ValidationError({
                'termination_date': _('Termination date cannot be before hire date')
            })
        
        return cleaned_data

# apps/employees/forms.py - Simplified version

from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Department, Position


class EmployeeFilterForm(forms.Form):
    """
    Filter form for employee list with Material Design styling.
    Simplified version without certifications.
    """
    
    EMPLOYMENT_TYPE_CHOICES = [
        ('', _('All Types')),
        ('full_time', _('Full-time')),
        ('part_time', _('Part-time')),
        ('contractor', _('Contractor')),
        ('intern', _('Intern')),
    ]
    
    STATUS_CHOICES = [
        ('', _('All Status')),
        ('active', _('Active')),
        ('inactive', _('Inactive')),
    ]
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Search by name, ID, or email...'),
            'autocomplete': 'off',
        }),
        label=_('Search')
    )
    
    department = forms.ModelChoiceField(
        queryset=Department.objects.filter(is_active=True),
        required=False,
        empty_label=_('All Departments'),
        widget=forms.Select(attrs={
            'class': 'form-select',
        }),
        label=_('Department')
    )
    
    position = forms.ModelChoiceField(
        queryset=Position.objects.filter(is_active=True),
        required=False,
        empty_label=_('All Positions'),
        widget=forms.Select(attrs={
            'class': 'form-select',
        }),
        label=_('Position')
    )
    
    employment_type = forms.ChoiceField(
        choices=EMPLOYMENT_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
        }),
        label=_('Employment Type')
    )
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select',
        }),
        label=_('Status')
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Material Design classes
        for field_name, field in self.fields.items():
            if field_name != 'search':
                field.widget.attrs['class'] = field.widget.attrs.get('class', '') + ' form-select-sm'

class EmployeeDocumentForm(forms.ModelForm):
    """Form for employee documents."""
    
    class Meta:
        model = EmployeeDocument
        fields = (
            'document_type', 'title', 'description',
            'file', 'issue_date', 'expiry_date'
        )
        widgets = {
            'document_type': forms.Select(attrs={
                'class': 'form-select'
            }),
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Document title')
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Document description')
            }),
            'file': forms.FileInput(attrs={
                'class': 'form-control'
            }),
            'issue_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'expiry_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        issue_date = cleaned_data.get('issue_date')
        expiry_date = cleaned_data.get('expiry_date')
        
        if issue_date and expiry_date and expiry_date < issue_date:
            raise ValidationError({
                'expiry_date': _('Expiry date cannot be before issue date')
            })
        
        return cleaned_data


class EmployeeSearchForm(forms.Form):
    """Form for searching/filtering employees."""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Search by name, email, or employee ID...'),
            'autocomplete': 'off'
        })
    )
    
    department = forms.ModelChoiceField(
        queryset=Department.objects.filter(is_active=True),
        required=False,
        empty_label=_('All Departments'),
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    position = forms.ModelChoiceField(
        queryset=Position.objects.filter(is_active=True),
        required=False,
        empty_label=_('All Positions'),
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    employment_type = forms.ChoiceField(
        required=False,
        choices=[('', _('All Types'))] + list(Employee._meta.get_field('employment_type').choices),
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    status = forms.ChoiceField(
        required=False,
        choices=[
            ('', _('All Statuses')),
            ('active', _('Active')),
            ('inactive', _('Inactive'))
        ],
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
class LocationForm(forms.ModelForm):
    """Form for creating/editing locations"""
    
    class Meta:
        model = Location
        fields = [
            'name',
            'address',
            'city',
            'postal_code',
            'country',
            'phone',
            'email',
            'manager',
            'labor_budget',
            'latitude',
            'longitude',
            'is_active',
            'notes',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('e.g., Toronto Clinic #1')
            }),
            'address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Street address')
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('City name')
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Postal/ZIP code')
            }),
            'country': forms.Select(attrs={
                'class': 'form-select'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Phone number')
            }),
            'email': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': _('contact@clinic.com')
            }),
            'manager': forms.Select(attrs={
                'class': 'form-select'
            }),
            'labor_budget': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01'
            }),
            'latitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '46.9479',
                'step': '0.000001'
            }),
            'longitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '7.4474',
                'step': '0.000001'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Internal notes about this location...')
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Make optional fields clearly marked
        self.fields['phone'].required = False
        self.fields['email'].required = False
        self.fields['manager'].required = False
        self.fields['manager'].empty_label = _('-- No manager assigned --')
        self.fields['latitude'].required = False
        self.fields['longitude'].required = False
        self.fields['notes'].required = False


class LocationSearchForm(forms.Form):
    """Form for searching/filtering locations"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': _('Search by name, city, or address...')
        })
    )
    
    country = forms.ChoiceField(
        required=False,
        choices=[('', _('All Countries'))] + Location._meta.get_field('country').choices,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    is_active = forms.ChoiceField(
        required=False,
        choices=[
            ('', _('All Status')),
            ('true', _('Active')),
            ('false', _('Inactive')),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )