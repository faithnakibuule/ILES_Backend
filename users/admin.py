from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, Course


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['name', 'created_at', 'updated_at']
    search_fields = ['name']


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = ['email', 'role', 'company', 'course', 'first_name', 'last_name', 'is_staff']

    fieldsets = (
        (None,       {'fields': ('email', 'password')}),
        ('Personal', {'fields': ('first_name', 'last_name', 'phone')}),
        ('Role',     {'fields': ('role', 'company', 'course')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'role', 'company', 'course', 'password1', 'password2'),
        }),
    )
    
    ordering = ['email']
    search_fields = ['email', 'first_name', 'last_name']
