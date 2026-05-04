from django.contrib.auth import get_user_model
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from placements.models import Company, InternshipPlacement
from reviews.models import Notification

from .models import College, Course, CustomUser

User = get_user_model()


class CustomUserSerializer(serializers.ModelSerializer):
    fullname = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    company = serializers.SerializerMethodField()
    course = serializers.SerializerMethodField()
    college = serializers.SerializerMethodField()

    def get_fullname(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()

    def get_full_name(self, obj):
        return self.get_fullname(obj)

    def get_company(self, obj):
        if not obj.company_id:
            return None
        return {
            "id": obj.company_id,
            "name": obj.company.name,
        }

    def get_course(self, obj):
        if not getattr(obj, "course_id", None):
            return None
        return {
            "id": obj.course_id,
            "name": obj.course.name,
            "college": (
                {
                    "id": obj.course.college_id,
                    "name": obj.course.college.name,
                }
                if getattr(obj.course, "college_id", None)
                else None
            ),
        }

    def get_college(self, obj):
        if getattr(obj, "college_id", None):
            return {
                "id": obj.college_id,
                "name": obj.college.name,
            }
        if getattr(obj, "course_id", None) and getattr(obj.course, "college_id", None):
            return {
                "id": obj.course.college_id,
                "name": obj.course.college.name,
            }
        return None

    class Meta:
        model = CustomUser
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "role",
            "fullname",
            "full_name",
            "phone",
            "company",
            "course",
            "college",
            "is_active",
        ]


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    confirm_password = serializers.CharField(write_only=True)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)
    company_id = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.all(),
        source="company",
        write_only=True,
        required=False,
        allow_null=True,
    )
    college_id = serializers.PrimaryKeyRelatedField(
        queryset=College.objects.all(),
        source="college",
        write_only=True,
        required=False,
        allow_null=True,
    )
    course_id = serializers.PrimaryKeyRelatedField(
        queryset=Course.objects.all(),
        source="course",
        write_only=True,
        required=False,
        allow_null=True,
    )
    course_name = serializers.CharField(
        write_only=True,
        required=False,
        allow_blank=True,
        allow_null=True,
    )

    class Meta:
        model = CustomUser
        fields = [
            "email",
            "role",
            "first_name",
            "last_name",
            "password",
            "confirm_password",
            "company_id",
            "college_id",
            "course_id",
            "course_name",
        ]

    def validate(self, data):
        if data["password"] != data["confirm_password"]:
            raise serializers.ValidationError("Passwords do not match.")

        if CustomUser.objects.filter(email=data["email"]).exists():
            raise serializers.ValidationError("Email already exists")

        if data.get("role") == "admin":
            raise serializers.ValidationError("Admin accounts cannot be created via registration.")

        role = data.get("role", "student")
        company = data.get("company")
        college = data.get("college")
        course = data.get("course")
        course_name = (data.get("course_name") or "").strip()

        if role == "student" and not course and course_name:
            course, _ = Course.objects.get_or_create(name=course_name, defaults={"college": college})
            data["course"] = course

        if role == "workplace_supervisor" and not company:
            raise serializers.ValidationError(
                {"company_id": "Workplace supervisors must select a company during registration."}
            )

        if role != "workplace_supervisor" and company:
            raise serializers.ValidationError(
                {"company_id": "Only workplace supervisors can select a company."}
            )

        if role == "academic_supervisor" and not college:
            raise serializers.ValidationError(
                {"college_id": "Academic supervisors must select a college during registration."}
            )

        if role != "academic_supervisor" and role != "student" and college:
            raise serializers.ValidationError(
                {"college_id": "Only students and academic supervisors can select a college."}
            )

        if role == "student":
            if not course:
                raise serializers.ValidationError(
                    {"course_id": "Students must select a course during registration."}
                )
            if college and getattr(course, "college_id", None) != college.id:
                raise serializers.ValidationError(
                    {"course_id": "Selected course does not belong to the selected college."}
                )
            if not college and getattr(course, "college_id", None):
                data["college"] = course.college
        elif course:
            raise serializers.ValidationError(
                {"course_id": "Only students can select a course."}
            )

        return data

    def create(self, validated_data):
        validated_data.pop("confirm_password")
        validated_data.pop("course_name", None)
        return CustomUser.objects.create_user(
            email=validated_data["email"],
            password=validated_data["password"],
            role=validated_data.get("role", "student"),
            first_name=validated_data.get("first_name", ""),
            last_name=validated_data.get("last_name", ""),
            company=validated_data.get("company"),
            course=validated_data.get("course"),
            college=validated_data.get("college"),
        )


class UserUpdateSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(required=False, allow_blank=True)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)

    class Meta:
        model = CustomUser
        fields = ["full_name", "first_name", "last_name", "phone"]

    def update(self, instance, validated_data):
        full_name = validated_data.pop("full_name", None)

        if full_name is not None:
            parts = full_name.strip().split(" ", 1)
            instance.first_name = parts[0]
            instance.last_name = parts[1] if len(parts) > 1 else ""

        if "first_name" in validated_data:
            instance.first_name = validated_data["first_name"]

        if "last_name" in validated_data:
            instance.last_name = validated_data["last_name"]

        if "phone" in validated_data:
            instance.phone = validated_data["phone"]

        instance.save()
        return instance


class AdminUserSerializer(serializers.ModelSerializer):
    company_id = serializers.PrimaryKeyRelatedField(
        queryset=Company.objects.all(),
        source="company",
        write_only=True,
        required=False,
        allow_null=True,
    )
    course_id = serializers.PrimaryKeyRelatedField(
        queryset=Course.objects.all(),
        source="course",
        write_only=True,
        required=False,
        allow_null=True,
    )
    college_id = serializers.PrimaryKeyRelatedField(
        queryset=College.objects.all(),
        source="college",
        write_only=True,
        required=False,
        allow_null=True,
    )
    company = serializers.SerializerMethodField()
    course = serializers.SerializerMethodField()
    college = serializers.SerializerMethodField()
    fullname = serializers.SerializerMethodField()
    password = serializers.CharField(write_only=True, required=False, allow_blank=False)

    class Meta:
        model = CustomUser
        fields = [
            "id",
            "email",
            "first_name",
            "last_name",
            "fullname",
            "role",
            "phone",
            "is_active",
            "company",
            "company_id",
            "course",
            "course_id",
            "college",
            "college_id",
            "password",
            "date_joined",
        ]
        read_only_fields = ["id", "fullname", "company", "course", "college", "date_joined"]

    def get_fullname(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()

    def get_company(self, obj):
        if not obj.company_id:
            return None
        return {
            "id": obj.company_id,
            "name": obj.company.name,
        }

    def get_course(self, obj):
        if not getattr(obj, "course_id", None):
            return None
        return {
            "id": obj.course_id,
            "name": obj.course.name,
            "college": (
                {
                    "id": obj.course.college_id,
                    "name": obj.course.college.name,
                }
                if getattr(obj.course, "college_id", None)
                else None
            ),
        }

    def get_college(self, obj):
        if getattr(obj, "college_id", None):
            return {
                "id": obj.college_id,
                "name": obj.college.name,
            }
        if getattr(obj, "course_id", None) and getattr(obj.course, "college_id", None):
            return {
                "id": obj.course.college_id,
                "name": obj.course.college.name,
            }
        return None

    def _has_open_student_placement(self, user):
        return InternshipPlacement.objects.filter(
            student=user,
            status__in=["PENDING", "ACTIVE"],
        ).exists()

    def _has_open_supervised_placements(self, user, relation_name):
        return InternshipPlacement.objects.filter(
            status__in=["PENDING", "ACTIVE"],
            **{relation_name: user},
        ).exists()

    def validate(self, attrs):
        role = attrs.get("role", getattr(self.instance, "role", None))
        company = attrs.get("company", getattr(self.instance, "company", None))
        course = attrs.get("course", getattr(self.instance, "course", None))
        college = attrs.get("college", getattr(self.instance, "college", None))

        if role == "student" and not course:
            raise serializers.ValidationError(
                {"course_id": "Students must be assigned to a course."}
            )

        if role == "workplace_supervisor" and not company:
            raise serializers.ValidationError(
                {"company_id": "Workplace supervisors must be assigned to a company."}
            )

        if role == "academic_supervisor" and not college:
            raise serializers.ValidationError(
                {"college_id": "Academic supervisors must be assigned to a college."}
            )

        if role != "workplace_supervisor" and "company" in attrs:
            attrs["company"] = None

        if role != "student" and "course" in attrs:
            attrs["course"] = None

        if role != "academic_supervisor" and role != "student" and "college" in attrs:
            attrs["college"] = None

        next_course = attrs.get("course", getattr(self.instance, "course", None))
        next_college = attrs.get("college", getattr(self.instance, "college", None))

        if role == "student" and next_course and next_college and getattr(next_course, "college_id", None) != next_college.id:
            raise serializers.ValidationError(
                {"course_id": "Selected course does not belong to the selected college."}
            )

        if role == "student" and next_course and "college" not in attrs:
            attrs["college"] = next_course.college

        if self.instance:
            if (
                role == "student"
                and "course" in attrs
                and attrs.get("course") != self.instance.course
                and self._has_open_student_placement(self.instance)
            ):
                raise serializers.ValidationError(
                    {"course_id": "This student's course cannot be changed while they have an active or pending placement."}
                )

            if (
                role == "workplace_supervisor"
                and "company" in attrs
                and attrs.get("company") != self.instance.company
                and self._has_open_supervised_placements(self.instance, "workplace_supervisor")
            ):
                raise serializers.ValidationError(
                    {"company_id": "This workplace supervisor's company cannot be changed while they supervise an active or pending placement."}
                )

            if (
                role == "academic_supervisor"
                and "college" in attrs
                and attrs.get("college") != self.instance.college
                and self._has_open_supervised_placements(self.instance, "academic_supervisor")
            ):
                raise serializers.ValidationError(
                    {"college_id": "This academic supervisor's college cannot be changed while they supervise an active or pending placement."}
                )

        if not self.instance and not attrs.get("password"):
            raise serializers.ValidationError({"password": "Password is required."})

        return attrs

    def create(self, validated_data):
        password = validated_data.pop("password")
        if validated_data.get("role") == "student" and validated_data.get("course") and not validated_data.get("college"):
            validated_data["college"] = validated_data["course"].college
        return CustomUser.objects.create_user(password=password, **validated_data)

    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)
        if validated_data.get("role", instance.role) == "student":
            next_course = validated_data.get("course", instance.course)
            if next_course and "college" not in validated_data:
                validated_data["college"] = next_course.college
        user = super().update(instance, validated_data)
        if password:
            user.set_password(password)
            user.save(update_fields=["password"])
        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token["email"] = user.email
        token["role"] = user.role
        token["full_name"] = f"{user.first_name} {user.last_name}".strip()
        return token

    def validate(self, attrs):
        data = super().validate(attrs)
        user_data = CustomUserSerializer(self.user).data
        data["user"] = user_data
        data["role"] = self.user.role
        data["email"] = self.user.email
        data["full_name"] = user_data.get("full_name", "")
        return data


class MeSerializer(serializers.ModelSerializer):
    unread_notifications = serializers.SerializerMethodField()
    fullname = serializers.SerializerMethodField()

    def get_unread_notifications(self, user):
        return Notification.objects.filter(
            recipient=user,
            is_read=False
        ).count()

    def get_fullname(self, obj):
        return f"{obj.first_name} {obj.last_name}".strip()

    class Meta:
        model = User
        fields = ["id", "email", "fullname", "role", "unread_notifications"]
        read_only_fields = fields


class CourseSerializer(serializers.ModelSerializer):
    college = serializers.SerializerMethodField(read_only=True)
    college_id = serializers.PrimaryKeyRelatedField(
        queryset=College.objects.all(),
        source="college",
        write_only=True,
        required=True,
    )

    class Meta:
        model = Course
        fields = ["id", "name", "college", "college_id"]
        read_only_fields = ["id"]

    def get_college(self, obj):
        if not getattr(obj, "college_id", None):
            return None
        return {
            "id": obj.college_id,
            "name": obj.college.name,
        }


class CollegeSerializer(serializers.ModelSerializer):
    academic_supervisor_count = serializers.IntegerField(read_only=True)
    course_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = College
        fields = ["id", "name", "academic_supervisor_count", "course_count"]
        read_only_fields = ["id", "academic_supervisor_count", "course_count"]
