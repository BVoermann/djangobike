from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import CustomUser


class CustomUserAdmin(BaseUserAdmin):
    """Admin interface for custom user model"""

    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'company_name')
        }),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'company_name')
        }),
    )

    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'is_staff']
    list_filter = BaseUserAdmin.list_filter + ('role',)


admin.site.register(CustomUser, CustomUserAdmin)
