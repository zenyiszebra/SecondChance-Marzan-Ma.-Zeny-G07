from django.contrib import admin

from .models import Inmate


@admin.register(Inmate)
class InmateAdmin(admin.ModelAdmin):
    list_display = ('inmate_number', 'last_name', 'first_name', 'status', 'created_by', 'created_at')
    list_filter = ('status',)
    search_fields = ('inmate_number', 'first_name', 'last_name')
