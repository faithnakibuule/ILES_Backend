import random
import string
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.utils import timezone

from placements.models import InternshipPlacement
from logbook.models import WeeklyLog
from reviews.models import Evaluation, EvaluationCriteria

User = get_user_model()

def _uid(length=6):
    return "".join(random.choices(string.ascii_lowercase + string.digits, k=length))

#def make_user(**kwargs):
    defaults = {
        "email":"user@example.com",
        "password":"pass1234",
    }
    defaults.update(kwargs)
    defaults.pop("username",None)
    password = defaults.pop("password")
    user = User.objects.create(**defaults)
    user.set_password(password)
    user.save()

    return user


def make_student(**kwargs):
    uid = _uid()
    defaults = {
        "email":      f"student_{uid}@test.com",
        "first_name": "Test",
        "last_name":  f"Student{uid}",
        "role":       "student",
        "password":   "testpass123",
    }
    defaults.update(kwargs)
    defaults.pop("username", None)
    password = defaults.pop("password")
    user = User.objects.create_user(**defaults)
    user.set_password(password)   # hashes the password — never store plain text
    user.save()
    return user

def make_supervisor(**kwargs):
    uid = _uid()
    defaults = {
        "email": kwargs.pop("email",f"supervisor_{uid}@test.com"),
        "first_name": kwargs.pop("first_name", "Test"),
        "last_name":  kwargs.pop("last_name", "Supervisor"),
        "role": "workplace_supervisor",
        "password": "testpass123",
    }
    defaults.update(kwargs)
    defaults.pop("username",None)
    password = defaults.pop("password")
    user = User.objects.create(**defaults)
    user.set_password(password)
    user.save()
    return user

def make_academic(**kwargs):
    uid = _uid()
    defaults = {
        "email": kwargs.pop("email",f"academic_{uid}@test.com"),
        "first_name": kwargs.pop("first_name", "Test"),
        "last_name":  kwargs.pop("last_name", "Academic"),
        "role":     "academic_supervisor",
        "password": "testpass123",
    }
    defaults.update(kwargs)
    defaults.pop("username",None)
    password = defaults.pop("password")
    user = User.objects.create(**defaults)
    user.set_password(password)
    user.save()
    return user

def make_admin(**kwargs):
    uid = _uid()
    defaults = {
        "email": kwargs.pop("email", f"admin_{uid}@test.com"),
        "first_name": kwargs.pop("first_name", "Test"),
        "last_name":  kwargs.pop("last_name", "Admin"),
        "role":       "admin",
        "is_staff":   True,
        "password":   "testpass123",
    }
    defaults.update(kwargs)
    defaults.pop("username",None)
    password = defaults.pop("password")
    user = User.objects.create(**defaults)
    user.set_password(password)
    user.save()
    return user

def make_placement(student, supervisor, **kwargs):
    today = date.today()
    default_academic = kwargs.pop(
        "academic_supervisor",
        User.objects.filter(role="academic_supervisor").order_by("-id").first(),
    )
    defaults = {
        "student":              student,
        "workplace_supervisor": supervisor,
        "academic_supervisor":  default_academic,
        "company_name":         kwargs.pop("company_name", "Test Company Ltd"),
        "start_date":           kwargs.pop("start_date",   today),
        "end_date":             kwargs.pop("end_date",     today + timedelta(weeks=12)),
        "status":               kwargs.pop("status",       "ACTIVE"),
    }
    defaults.update(kwargs)
    return InternshipPlacement.objects.create(**defaults)

_week_counter = {}  # maps student.id → next week number

def make_log(student, placement, status="DRAFT", **kwargs):
    # Auto-assign week number per student
    student_id = student.id
    if student_id not in _week_counter:
        _week_counter[student_id] = 1
    week_number = kwargs.pop("week_number", _week_counter[student_id])
    _week_counter[student_id] += 1

    defaults = {
        "intern":          student,
        "placement":       placement,
        "week_number":     week_number,
        "activities":      kwargs.pop("activities",      f"Worked on project tasks for week {week_number}."),
        "learning_points": kwargs.pop("learning_points", f"Learned new skills in week {week_number}."),
        "status":          status,
    }

    if status in ("SUBMITTED", "REVIEWED", "APPROVED"):
        defaults["submitted_at"] = kwargs.pop(
            "submitted_at", timezone.now() - timedelta(days=3)
        )

    defaults.update(kwargs)
    return WeeklyLog.objects.create(**defaults)

def make_criteria():
    criteria_data = [
        ("Technical Skills",   Decimal("30"), 100),
        ("Communication",      Decimal("20"), 100),
        ("Punctuality",        Decimal("15"), 100),
        ("Initiative",         Decimal("20"), 100),
        ("Professionalism",    Decimal("15"), 100),
    ]
    criteria = []
    for name, weight, max_score in criteria_data:
        obj, _ = EvaluationCriteria.objects.get_or_create(
            name=name,
            defaults={
                "description": f"Assessment of {name.lower()}.",
                "max_score":   max_score,
                "weight":      weight,
            }
        )
        criteria.append(obj)
    return criteria

def make_evaluation(log, academic_supervisor, criteria=None, **kwargs):
    if criteria is None:
        criteria = make_criteria()
    

    # Default scores: 75 on every criterion
    scores = kwargs.pop(
        "criteria_scores",
        {str(c.id): 75 for c in criteria}
    )
    
    if "score" in kwargs and "total_score" not in kwargs:
        kwargs["total_score"] = kwargs.pop("score")

    if "total_score" in kwargs:
        total_score = kwargs.pop("total_score")
    else:
        total_score = round(
            sum(
                (scores.get(str(c.id),0)/ c.max_score) * float(c.weight)
                for c in criteria
            ),
            2
        )



    if log.status != "APPROVED":
        log.status = "APPROVED"
        log.save(update_fields=["status"])

    defaults = {
        "log": log,
        "academic_supervisor":academic_supervisor,
        "criteria_scores":scores,
        "total_score":total_score,
        "comments":kwargs.pop("comments", "Good work overall."),
    }
    defaults.update(kwargs)
    return Evaluation.objects.create(**defaults)

def reset_week_counter():
    global _week_counter
    _week_counter = {}
