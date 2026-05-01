# logbook/signals.py
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import WeeklyLog
from reviews.models import Notification
from users.email_utils import (
    send_log_submitted_email,
    send_log_reviewed_email,
    send_log_sent_back_email,
    send_log_approved_email,
)


@receiver(pre_save, sender=WeeklyLog)
def capture_old_status(sender, instance, **kwargs):
    """Store the old status on the instance before the save overwrites it."""
    if instance.pk:
        try:
            instance._old_status = WeeklyLog.objects.get(pk=instance.pk).status
        except WeeklyLog.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None  # brand new object


@receiver(post_save, sender=WeeklyLog)
def handle_log_status_notifications(sender, instance, created, **kwargs):
    if created:
        return

    old_status = getattr(instance, '_old_status', None)
    new_status = instance.status

    # Skip if status did not actually change
    if old_status == new_status:
        return

    student = instance.intern

    # ── DRAFT → SUBMITTED ─────────────────────────────────────────────────────
    if old_status == 'DRAFT' and new_status == 'SUBMITTED':
        supervisor = instance.placement.workplace_supervisor
        if supervisor:
            Notification.objects.create(
                recipient=supervisor,
                message=(
                    f"{student.first_name} {student.last_name} submitted "
                    f"their Week {instance.week_number} log."
                ),
                notification_type='LOG_SUBMITTED',
                is_read=False,
            )
            # Email the supervisor so they know even if not logged in
            send_log_submitted_email(student, supervisor, instance.week_number)

    # ── SUBMITTED → REVIEWED ──────────────────────────────────────────────────
    elif old_status == 'SUBMITTED' and new_status == 'REVIEWED':
        academic = getattr(instance.placement, 'academic_supervisor', None)
        if academic:
            Notification.objects.create(
                recipient=academic,
                message=(
                    f"{student.first_name} {student.last_name}'s "
                    f"Week {instance.week_number} log is ready for scoring."
                ),
                notification_type='LOG_REVIEWED',
                is_read=False,
            )
            # Email the academic supervisor
            send_log_reviewed_email(student, academic, instance.week_number)

    # ── REVIEWED → APPROVED ───────────────────────────────────────────────────
    elif old_status == 'REVIEWED' and new_status == 'APPROVED':
        # Fetch score from latest evaluation if it exists
        latest_eval = instance.evaluations.order_by('-created_at').first()
        score = round(latest_eval.total_score, 1) if latest_eval else 'N/A'

        Notification.objects.create(
            recipient=student,
            message=(
                f"Your Week {instance.week_number} log has been approved. "
                f"Score: {score}/100"
            ),
            notification_type='LOG_APPROVED',
            is_read=False,
        )
        # Email the student their score
        send_log_approved_email(student, instance.week_number, score)

    # ── SUBMITTED → DRAFT (sent back) ─────────────────────────────────────────
    elif old_status == 'SUBMITTED' and new_status == 'DRAFT':
        from reviews.models import ReviewAction
        last_action = ReviewAction.objects.filter(
            log=instance,
            action='SENT_BACK',
        ).order_by('-timestamp').first()
        comment = last_action.comment if last_action else "Please review and resubmit."

        Notification.objects.create(
            recipient=student,
            message=(
                f"Your Week {instance.week_number} log was sent back. "
                f"Reason: {comment}"
            ),
            notification_type='LOG_SENT_BACK',
            is_read=False,
        )
        # Email the student the supervisor's comment
        send_log_sent_back_email(student, instance.week_number, comment)