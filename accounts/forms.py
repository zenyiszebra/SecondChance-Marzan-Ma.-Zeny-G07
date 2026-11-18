from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.core.files.uploadedfile import UploadedFile

from .models import User

MAX_PHOTO_MB = 2


class BootstrapFormMixin:
    """Adds Bootstrap classes to every widget."""

    def apply_bootstrap(self):
        for field in self.fields.values():
            css = 'form-select' if isinstance(field.widget, forms.Select) else 'form-control'
            existing = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = f'{existing} {css}'.strip()


class RegisterForm(BootstrapFormMixin, UserCreationForm):
    # Admin is not offered here: admins are created with `createsuperuser`.
    role = forms.ChoiceField(
        label='Register as',
        choices=[c for c in User.Role.choices if c[0] != User.Role.ADMIN],
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('first_name', 'last_name', 'username', 'email', 'contact_number', 'role')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ('first_name', 'last_name', 'email'):
            self.fields[name].required = True
        self.apply_bootstrap()

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError('An account with this email already exists.')
        return email


class LoginForm(BootstrapFormMixin, AuthenticationForm):
    error_messages = {
        **AuthenticationForm.error_messages,
        'invalid_login': 'Invalid username or password. Please try again.',
    }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.apply_bootstrap()


class ProfileForm(BootstrapFormMixin, forms.ModelForm):
    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'contact_number', 'profile_photo')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ('first_name', 'last_name', 'email'):
            self.fields[name].required = True
        self.apply_bootstrap()

    def clean_email(self):
        email = self.cleaned_data['email'].strip().lower()
        taken = User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk)
        if taken.exists():
            raise forms.ValidationError('Another account already uses this email.')
        return email

    def clean_profile_photo(self):
        photo = self.cleaned_data.get('profile_photo')
        if isinstance(photo, UploadedFile) and photo.size > MAX_PHOTO_MB * 1024 * 1024:
            raise forms.ValidationError(f'Photo must be {MAX_PHOTO_MB} MB or smaller.')
        return photo
