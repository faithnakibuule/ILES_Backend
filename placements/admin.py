from django.contrib import admin
from .models import InternshipPlacement

# Register your models here.

@admin.register(InternshipPlacement)
class InternshipPlacementAdmin(admin.ModelAdmin):
    list_display = ['student' , 'company_name' , 'status', 'start_date','end_date']
