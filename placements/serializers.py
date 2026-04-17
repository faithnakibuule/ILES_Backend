# placements/serializers.py

from tracemalloc import start

from rest_framework import serializers
from .models import InternshipPlacement
from users.serializers import CustomUserSerializer

class PlacementSerializer(serializers.ModelSerializer):
    # Nested read-only: shows full user object instead of just an ID
    student = CustomUserSerializer(read_only=True)
    workplace_supervisor = CustomUserSerializer(read_only=True)

    # Write-only fields to accept IDs when creating/updating
    student_id = serializers.PrimaryKeyRelatedField(
        queryset=InternshipPlacement.student.field.related_model.objects.all(),
        source='student',
        write_only=True
    )
    workplace_supervisor_id = serializers.PrimaryKeyRelatedField(
        queryset=InternshipPlacement.workplace_supervisor.field.related_model.objects.all(),
        source='workplace_supervisor',
        write_only=True
    )

    class Meta:
        model = InternshipPlacement
        fields = [
            'id',
            'student',
            'student_id',
            'workplace_supervisor',
            'workplace_supervisor_id',
            'company_name',
            'start_date',
            'end_date',
            'status',
        ]

    def validate(self, data):
        """
        Check that end_date is after start_date.
        Object-level validation: sees all fields together.
        """
        start_date = data.get('start_date')
        end_date = data.get('end_date')

        if start_date is not None and end_date is not None:
            if start_date >= end_date:
                raise serializers.ValidationError("End date must be after start date")
        
        return data
