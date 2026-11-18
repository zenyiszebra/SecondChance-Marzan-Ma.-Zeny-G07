from django.contrib.auth.models import AbstractUser, UserManager
from django.core.validators import RegexValidator
from django.db import models


class SecondChanceUserManager(UserManager):
    """Users made with `createsuperuser` automatically get the Admin role."""

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('role', User.Role.ADMIN)
        return super().create_superuser(username, email, password, **extra_fields)


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        STAFF = 'staff', 'Staff'
        REVIEWER = 'reviewer', 'Reviewer'

    email = models.EmailField('email address', unique=True)
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STAFF)
    contact_number = models.CharField(
        max_length=20,
        blank=True,
        validators=[
            RegexValidator(
                r'^\+?[0-9\s\-]{7,15}$',
                'Enter a valid contact number (7 to 15 digits, spaces or dashes allowed).',
            )
        ],
    )
    profile_photo = models.ImageField(upload_to='profile_photos/', blank=True, null=True)

    objects = SecondChanceUserManager()

    REQUIRED_FIELDS = ['email']

    @property
    def dashboard_url_name(self):
        return {
            self.Role.ADMIN: 'accounts:admin_dashboard',
            self.Role.STAFF: 'accounts:staff_dashboard',
            self.Role.REVIEWER: 'accounts:reviewer_dashboard',
        }.get(self.role, 'accounts:profile')

    def __str__(self):
        return f'{self.username} ({self.get_role_display()})'
