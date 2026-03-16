# placements/serializers.py
# Converts InternshipPlacement model objects into JSON
# that the React frontend can read and understand.

from rest_framework import serializers
from .models import InternshipPlacement


class PlacementSerializer(serializers.ModelSerializer):
    # Add human-readable names for the foreign key fields
    # so the frontend gets "Alice Nakato" not just a user ID number
    student_name     = serializers.CharField(
        source='student.get_full_name', read_only=True
    )
    supervisor_name  = serializers.CharField(
        source='workplace_supervisor.get_full_name', read_only=True
    )

    class Meta:
        model  = InternshipPlacement
        fields = [
            'id',
            'student',
            'student_name',
            'workplace_supervisor',
            'supervisor_name',
            'company_name',
            'start_date',
            'end_date',
            'status',
        ]