# logbook/filters.py — create this new file

import django_filters
from .models import WeeklyLog

class WeeklyLogFilter(django_filters.FilterSet):
    submitted_after = django_filters.DateFilter(
        field_name='submitted_at',
        method='filter_submitted_after'
    )
    submitted_before = django_filters.DateFilter(
        field_name='submitted_at',
        method='filter_submitted_before'
    )

    def filter_submitted_after(self, queryset, name, value):
        if value:
            return queryset.filter(submitted_at__date__gte=value)
        return queryset

    def filter_submitted_before(self, queryset, name, value):
        if value:
            return queryset.filter(submitted_at__date__lte=value)
        return queryset

    class Meta:
        model = WeeklyLog
        fields = ['status', 'week_number', 'submitted_after', 'submitted_before']
