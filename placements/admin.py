from django.contrib import admin
<<<<<<< HEAD

# Register your models here.
=======
from .models import InternshipPlacement

# Register your models here.

@admin.register(InternshipPlacement)
class InternshipPlacementAdmin(admin.ModelAdmin):
    list_display = ['student' , 'company_name' , 'status', 'start_date','end_date']
>>>>>>> 37ef7494ad109a3cf8f1ecfdf572aa9674e4feda
