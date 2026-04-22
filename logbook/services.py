from datetime import datetime, time, timedelta

from django.utils import timezone

from placements.models import InternshipPlacement

from .models import WeeklyLog


REQUIRED_LOG_FIELDS = ("activities", "learning_points")


def can_transition(log, new_status, user_role):
    if user_role == "student":
        if log.status == "DRAFT" and new_status == "SUBMITTED":
            return True

    elif user_role == "workplace_supervisor":
        if log.status == "SUBMITTED" and new_status == "REVIEWED":
            return True
        if log.status == "SUBMITTED" and new_status == "DRAFT":
            return True

    elif user_role == "academic_supervisor":
        if log.status == "REVIEWED" and new_status == "APPROVED":
            return True

    return False


def server_now():
    return timezone.localtime()


def server_today():
    return timezone.localdate()


def get_active_placement(student, current_date=None):
    current_date = current_date or server_today()
    return (
        InternshipPlacement.objects.filter(
            student=student,
            status="ACTIVE",
            start_date__lte=current_date,
            end_date__gte=current_date,
        )
        .select_related("workplace_supervisor", "academic_supervisor")
        .order_by("-start_date", "-id")
        .first()
    )


def get_week_number_for_date(placement, current_date=None):
    current_date = current_date or server_today()
    delta_days = (current_date - placement.start_date).days
    if delta_days < 0:
        return 1
    return (delta_days // 7) + 1


def get_week_start(placement, week_number):
    return placement.start_date + timedelta(days=(week_number - 1) * 7)


def get_week_end(placement, week_number):
    return get_week_start(placement, week_number) + timedelta(days=6)


def get_week_deadline(placement, week_number):
    week_end = get_week_end(placement, week_number)
    naive_deadline = datetime.combine(week_end, time(23, 59, 59, 999999))
    return timezone.make_aware(naive_deadline, timezone.get_current_timezone())


def is_log_complete(log):
    return all((getattr(log, field) or "").strip() for field in REQUIRED_LOG_FIELDS)


def finalize_expired_logs(now=None):
    now = now or server_now()
    processed = []

    drafts = (
        WeeklyLog.objects.select_related("placement", "intern")
        .filter(status="DRAFT")
        .filter(placement__status__in=["ACTIVE", "COMPLETED"])
    )

    for log in drafts:
        deadline = get_week_deadline(log.placement, log.week_number)
        if now <= deadline:
            continue

        if is_log_complete(log):
            log.status = "SUBMITTED"
            log.submitted_at = deadline
        else:
            log.status = "MISSED"
        log.save(update_fields=["status", "submitted_at"])
        processed.append(log.id)

    return processed


def student_can_edit_log(log, now=None):
    now = now or server_now()
    if log.status != "DRAFT":
        return False
    return now <= get_week_deadline(log.placement, log.week_number)


def get_current_week_log(student, current_date=None):
    placement = get_active_placement(student, current_date=current_date)
    if not placement:
        return None, None, None

    week_number = get_week_number_for_date(placement, current_date=current_date)
    log = WeeklyLog.objects.filter(
        intern=student,
        placement=placement,
        week_number=week_number,
    ).first()
    return placement, week_number, log


def get_missed_week_numbers(student, placement=None, current_date=None):
    current_date = current_date or server_today()
    placement = placement or get_active_placement(student, current_date=current_date)
    if not placement:
        return []

    current_week = get_week_number_for_date(placement, current_date=current_date)
    elapsed_weeks = current_week - 1
    if elapsed_weeks <= 0:
        return []

    logs = WeeklyLog.objects.filter(
        intern=student,
        placement=placement,
        week_number__lte=elapsed_weeks,
    ).values_list("week_number", "status")

    logged_weeks = {week for week, status in logs if status != "MISSED"}
    explicit_missed_weeks = {week for week, status in logs if status == "MISSED"}

    missed = []
    for week_number in range(1, elapsed_weeks + 1):
        if week_number in explicit_missed_weeks or week_number not in logged_weeks:
            missed.append(week_number)
    return missed


def build_student_logbook_summary(student, current_date=None):
    placement, current_week, current_log = get_current_week_log(
        student, current_date=current_date
    )

    if not placement:
        return {
            "has_active_placement": False,
            "placement": None,
            "current_week": None,
            "current_log_id": None,
            "current_week_deadline": None,
            "missed_weeks": [],
        }

    return {
        "has_active_placement": True,
        "placement": placement,
        "current_week": current_week,
        "current_log_id": current_log.id if current_log else None,
        "current_week_deadline": get_week_deadline(placement, current_week),
        "missed_weeks": get_missed_week_numbers(
            student, placement=placement, current_date=current_date
        ),
    }
