# logbook/filters.py — create this new file

import django_filters
from .models import WeeklyLog

class WeeklyLogFilter(django_filters.FilterSet):
    submitted_after = django_filters.DateFilter(
        field_name='submitted_at',
        lookup_expr='date__gte'
    )
    submitted_before = django_filters.DateFilter(
        field_name='submitted_at',
        lookup_expr='date__lt'
    )

    class Meta:
        model = WeeklyLog
        fields = ['status', 'week_number', 'submitted_after', 'submitted_before']