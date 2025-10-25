"""
Forms for employee management.
"""

from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

from apps.accounts.models import User
from .models import Department, Location, Position, Employee, EmployeeDocument


class DepartmentForm(forms.ModelForm):
    """Department creation and update form."""
    
    class Meta:
        model = Department
        fields = [
            'name',
            'code',
            'description',
            'manager',
            'phone_extension',
            'location_notes',
            'is_active',
            'effective_from',
            'effective_to',
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Enter department name')
            }),
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('e.g., ADM, RAD, CARD')
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': _('Brief description of the department')
            }),
            'manager': forms.Select(attrs={
                'class': 'form-select'
            }),
            'phone_extension': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('e.g., 1234')
            }),
            'location_notes': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 2,
                'placeholder': _('Building, floor, room details')
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'effective_from': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'effective_to': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # English: Only active users can be managers
        self.fields['manager'].queryset = User.objects.filter(
            is_active=True
        ).order_by('first_name', 'last_name')
        
        # English: Set labels
        self.fields['name'].label = _('Department Name')
        self.fields['code'].label = _('Department Code')
        self.fields['description'].label = _('Description')
        self.fields['manager'].label = _('Department Manager')
        self.fields['phone_extension'].label = _('Phone Extension')
        self.fields['location_notes'].label = _('Location Notes')
        self.fields['is_active'].label = _('Active')
        self.fields['effective_from'].label = _('Effective From')
        self.fields['effective_to'].label = _('Effective To')
        
        # English: Help texts
        self.fields['code'].help_text = _('Short code for department (3-4 characters)')
        self.fields['manager'].help_text = _('Select the manager for this department')
        self.fields['manager'].empty_label = _('— No manager assigned —')
        self.fields['effective_to'].help_text = _('Leave empty if ongoing')
    
    def clean_code(self):
        """Validate department code."""
        code = self.cleaned_data.get('code')
        if code:
            code = code.upper()
            # English: Check for duplicate codes (excluding current instance)
            qs = Department.objects.filter(code=code)
            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise forms.ValidationError(_('A department with this code already exists.'))
        return code
    
    def clean(self):
        """Validate date range."""
        cleaned_data = super().clean()
        effective_from = cleaned_data.get('effective_from')
        effective_to = cleaned_data.get('effective_to')
        
        if effective_from and effective_to:
            if effective_to < effective_from:
                raise forms.ValidationError({
                    'effective_to': _('End date must be after start date.')
                })
        
        return cleaned_data

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


class EmployeeFilterForm(forms.Form):
    """
    Filter form for employee list with Material Design styling.
    Includes location filter.
    """

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

    location = forms.ModelChoiceField(
        queryset=Location.objects.filter(is_active=True),
        required=False,
        empty_label=_('All Locations'),
        widget=forms.Select(attrs={
            'class': 'form-select',
        }),
        label=_('Location')
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
        required=False,
        choices=[('', _('All Types'))] + [
            ('FT', _('Full-time')),
            ('PT', _('Part-time')),
            ('CT', _('Contract')),
            ('TM', _('Temporary')),
            ('IN', _('Intern')),
        ],
        widget=forms.Select(attrs={
            'class': 'form-select',
        }),
        label=_('Type')
    )

    status = forms.ChoiceField(
        required=False,
        choices=[
            ('', _('All Statuses')),
            ('active', _('Active')),
            ('inactive', _('Inactive'))
        ],
        widget=forms.Select(attrs={
            'class': 'form-select',
        }),
        label=_('Status')
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # English: Add Material Design classes for better styling
        for field_name, field in self.fields.items():
            if field_name != 'search':
                current_class = field.widget.attrs.get('class', '')
                field.widget.attrs['class'] = f"{current_class} form-select-sm"


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
        choices=[('', _('All Types'))] +
        list(Employee._meta.get_field('employment_type').choices),
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
            'code',
            'address',
            'address_line_2',
            'city',
            'postal_code',
            'state_province',
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
            'code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('e.g., TOR1, GVA, LAU')
            }),
            'address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Street address')
            }),
            'address_line_2': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Apartment, suite, unit, floor (optional)')
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('City name')
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Postal/ZIP code')
            }),
            'state_province': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('State/Province/Canton code (e.g., VD, QC, NY)')
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

        # If editing existing location with address_detail, populate address fields from it
        if self.instance and self.instance.pk and self.instance.address_detail:
            addr = self.instance.address_detail
            self.initial['address'] = addr.address
            self.initial['address_line_2'] = addr.address_line_2
            self.initial['city'] = addr.city
            self.initial['postal_code'] = addr.postal_code
            self.initial['state_province'] = addr.state_province
            self.initial['country'] = addr.country
            self.initial['latitude'] = addr.latitude
            self.initial['longitude'] = addr.longitude

    def save(self, commit=True):
        """
        Save Location and automatically create/update Address record.
        This maintains backward compatibility with the old address fields.
        """
        from apps.core.models import Address

        location = super().save(commit=False)

        # Create or update Address record from form data
        if location.address_detail_id:
            # Update existing address
            address = location.address_detail
            address.address = self.cleaned_data.get('address', '')
            address.address_line_2 = self.cleaned_data.get('address_line_2', '')
            address.city = self.cleaned_data.get('city', '')
            address.postal_code = self.cleaned_data.get('postal_code', '')
            address.state_province = self.cleaned_data.get('state_province', '')
            address.country = self.cleaned_data.get('country', 'CH')
            address.latitude = self.cleaned_data.get('latitude')
            address.longitude = self.cleaned_data.get('longitude')
            if commit:
                address.save()
        else:
            # Create new address
            address = Address.objects.create(
                address=self.cleaned_data.get('address', ''),
                address_line_2=self.cleaned_data.get('address_line_2', ''),
                city=self.cleaned_data.get('city', ''),
                postal_code=self.cleaned_data.get('postal_code', ''),
                state_province=self.cleaned_data.get('state_province', ''),
                country=self.cleaned_data.get('country', 'CH'),
                latitude=self.cleaned_data.get('latitude'),
                longitude=self.cleaned_data.get('longitude'),
            )
            location.address_detail = address

        if commit:
            location.save()

        return location


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
        choices=[('', _('All Countries'))] +
        Location._meta.get_field('country').choices,
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
