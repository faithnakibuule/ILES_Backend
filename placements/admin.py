from django.contrib import admin

from .models import Company, InternshipPlacement

# Register your models here.


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ["name", "created_at", "updated_at"]
    search_fields = ["name"]

@admin.register(InternshipPlacement)
class InternshipPlacementAdmin(admin.ModelAdmin):
    list_display = ['student' , 'company_name' , 'status', 'start_date','end_date']
    list_filter = ["status", "company"]
    search_fields = ["student__email", "student__first_name", "student__last_name", "company_name"]
