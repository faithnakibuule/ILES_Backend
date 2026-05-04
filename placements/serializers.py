from rest_framework import serializers
from django.utils import timezone

from users.models import CustomUser
from users.serializers import CustomUserSerializer

from .models import Company, InternshipPlacement


class CompanySerializer(serializers.ModelSerializer):
    supervisor_count = serializers.IntegerField(read_only=True)
    supervisors = serializers.SerializerMethodField(read_only=True)
    supervisor_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False,
    )

    class Meta:
        model = Company
        fields = ["id", "name", "supervisor_count", "supervisors", "supervisor_ids"]

    def get_supervisors(self, obj):
        """Get all workplace supervisors assigned to this company."""
        supervisors = obj.users.filter(role="workplace_supervisor")
        return CustomUserSerializer(supervisors, many=True).data


class PlacementSerializer(serializers.ModelSerializer):
    student = CustomUserSerializer(read_only=True)
    workplace_supervisor = CustomUserSerializer(read_only=True)
    academic_supervisor = CustomUserSerializer(read_only=True)
    company = CompanySerializer(read_only=True)

    student_id = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.filter(role="student"),
        source="student",
        write_only=True,
    )
    workplace_supervisor_id = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.filter(role="workplace_supervisor").select_related("company"),
        source="workplace_supervisor",
        write_only=True,
    )
    academic_supervisor_id = serializers.PrimaryKeyRelatedField(
        queryset=CustomUser.objects.filter(role="academic_supervisor"),
        source="academic_supervisor",
        write_only=True,
        required=False,
        allow_null=True,
    )
    company_id = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.all(),
        source="company",
        write_only=True,
        required=False,
        allow_null=True,
    )

    class Meta:
        model = InternshipPlacement
        fields = [
            "id",
            "student",
            "student_id",
            "workplace_supervisor",
            "workplace_supervisor_id",
            "academic_supervisor",
            "academic_supervisor_id",
            "company",
            "company_id",
            "company_name",
            "start_date",
            "end_date",
            "status",
        ]
        read_only_fields = ["status"]
        extra_kwargs = {
            "company_name": {"required": False, "allow_blank": True},
        }
    def validate(self, attrs):
        instance = getattr(self, "instance", None)
        student = attrs.get("student", getattr(instance, "student", None))
        supervisor = attrs.get(
            "workplace_supervisor",
            getattr(instance, "workplace_supervisor", None),
        )
        company = attrs.get("company", getattr(instance, "company", None))
        company_name = attrs.get("company_name", getattr(instance, "company_name", "")).strip()
        start_date = attrs.get("start_date", getattr(instance, "start_date", None))
        end_date = attrs.get("end_date", getattr(instance, "end_date", None))
        incoming_status = self.initial_data.get("status") if hasattr(self, "initial_data") else None

        if start_date and end_date and start_date >= end_date:
            raise serializers.ValidationError("End date must be after start date.")

        if not company and not company_name:
            raise serializers.ValidationError(
                {"company_id": "Company is required.", "company_name": "Company is required."}
            )

        if not company and company_name:
            company, _ = Company.objects.get_or_create(name=company_name)
            attrs["company"] = company

        if supervisor and not supervisor.company_id:
            raise serializers.ValidationError(
                {
                    "workplace_supervisor_id": (
                        "Selected workplace supervisor is not assigned to a company."
                    )
                }
            )

        if supervisor and supervisor.company_id != company.id:
            raise serializers.ValidationError(
                {
                    "workplace_supervisor_id": (
                        "Selected workplace supervisor is not assigned to that company."
                    )
                }
            )

        if student:
            today = timezone.localdate()
            existing = InternshipPlacement.objects.filter(
                student=student,
            ).exclude(status="CANCELLED").filter(end_date__gte=today)
            if instance:
                existing = existing.exclude(pk=instance.pk)
            if existing.exists():
                raise serializers.ValidationError(
                    {
                        "student_id": (
                            "This student already has a current or upcoming placement."
                        )
                    }
                )

        if incoming_status not in (None, ""):
            raise serializers.ValidationError(
                {
                    "status": (
                        "Placement status is managed automatically from the dates. "
                        "Use the cancel action to cancel a placement."
                    )
                }
            )

        return attrs

    def create(self, validated_data):
        company = validated_data.get("company")
        if company:
            validated_data["company_name"] = company.name
        return super().create(validated_data)

    def update(self, instance, validated_data):
        company = validated_data.get("company", instance.company)
        if company:
            validated_data["company_name"] = company.name
        return super().update(instance, validated_data)
