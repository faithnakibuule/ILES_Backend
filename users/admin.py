from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['email', 'role', 'company', 'first_name', 'last_name', 'is_staff']

    fieldsets = (
        (None,       {'fields': ('email', 'password')}),
        ('Personal', {'fields': ('first_name', 'last_name', 'phone')}),
        ('Role',     {'fields': ('role', 'company')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'role', 'company', 'password1', 'password2'),
        }),
    )
    
    ordering = ['email']
    search_fields = ['email', 'first_name', 'last_name']
