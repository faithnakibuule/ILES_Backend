# logbook/signals.py — add this at the top, alongside post_save

from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import WeeklyLog
from reviews.models import Notification


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

    if old_status == new_status:
        return

    # DRAFT → SUBMITTED
    if old_status == 'DRAFT' and new_status == 'SUBMITTED':
        supervisor = instance.placement.workplace_supervisor
        Notification.objects.create(
            recipient=supervisor,
            message=f"{instance.intern.email} submitted their Week {instance.week_number} log.",
            notification_type='LOG_SUBMITTED',
            is_read=False
        )

    # SUBMITTED → REVIEWED
    elif old_status == 'SUBMITTED' and new_status == 'REVIEWED':
        academic_sup = instance.intern.academic_supervisor
        if academic_sup:
            Notification.objects.create(
                recipient=academic_sup,
                message=f"{instance.intern.email}'s Week {instance.week_number} log is ready for scoring.",
                notification_type='LOG_REVIEWED',
                is_read=False
            )

    # REVIEWED → APPROVED
    elif old_status == 'REVIEWED' and new_status == 'APPROVED':
        Notification.objects.create(
            recipient=instance.intern,
            message=f"Your Week {instance.week_number} log has been approved and scored.",
            notification_type='LOG_APPROVED',
            is_read=False
        )

    # SUBMITTED → DRAFT (sent back)
    elif old_status == 'SUBMITTED' and new_status == 'DRAFT':
        from reviews.models import ReviewAction
        last_action = ReviewAction.objects.filter(
            log=instance, action='SENT_BACK'
        ).order_by('-timestamp').first()
        comment = last_action.comment if last_action else "Please review and resubmit."

        Notification.objects.create(
            recipient=instance.intern,
            message=f"Your Week {instance.week_number} log was sent back. Reason: {comment}",
            notification_type='LOG_SENT_BACK',
            is_read=False
        )
        