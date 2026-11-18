from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ('username', 'email', 'role', 'is_active', 'date_joined')
    list_filter = ('role', 'is_active')
    fieldsets = DjangoUserAdmin.fieldsets + (
        ('SecondChance', {'fields': ('role', 'contact_number', 'profile_photo')}),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        ('SecondChance', {'fields': ('email', 'role', 'contact_number')}),
    )
