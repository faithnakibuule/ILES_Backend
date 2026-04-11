# logbook/signals.py

from django.db.models.signals import post_save   # The signal that fires AFTER a model saves
from django.dispatch import receiver              # The decorator that connects function to signal
from .models import WeeklyLog                     # The model we are listening to
from reviews.models import Notification  


# get the review action comment for a log(used when sending back, to include the reason)

def get_latest_sendback_comment(log):
    from reviews.models import ReviewAction
    last_action = ReviewAction.objects.filter(
        log = log,
        action = "SENT_BACK"
    ).order_by("-timestamp").first()
    return last_action.comment if last_action else "Please review and resubmit." 
             # The model we are writing to


@receiver(post_save, sender=WeeklyLog)
# This decorator says: "Hey Django, whenever WeeklyLog is saved, call this function"
def notify_supervisor_on_submission(sender, instance, created, **kwargs):
    
    # STEP 1: Ignore brand new logs
    # A new log is always DRAFT — never SUBMITTED
    # So if created=True, there's nothing to notify about
    if created:
        return

    # STEP 2: Fetch the OLD state of this log from the database
    # instance already has the NEW values in memory
    # We go back to the database to see what it looked like BEFORE this save
    try:
        old_log = WeeklyLog.objects.get(pk=instance.pk)
    except WeeklyLog.DoesNotExist:
        return

    # STEP 3: Check if status specifically changed from DRAFT to SUBMITTED
    # We only want to notify on THIS exact transition — not any other save
    if old_log.status != WeeklyLog.Status.DRAFT:
        return
    if instance.status != WeeklyLog.Status.SUBMITTED:
        return

    # STEP 4: Find the workplace supervisor through the placement
    # The chain is: WeeklyLog → Placement → supervisor
    supervisor = instance.placement.supervisor

    # STEP 5: Create the notification for the supervisor
    # This writes one row into the reviews_notification table
    Notification.objects.create(
        recipient=supervisor,
        notification_type=Notification.NotificationType.LOG_SUBMITTED,
        message=(
            f"A new log for Week {instance.week_number} "
            f"has been submitted by {instance.student.get_full_name()} "
            f"and is awaiting your review."
        )
    )

#REVIEWED notify academic supervisor
@receiver(post_save, sender=WeeklyLog)
def notify_on_reviewed(sender, instance, created, **kwargs):
    if instance.status == "REVIEWED":
        old_status = getattr(instance,"_old_status",None)
        if old_status != "REVIEWED":
            academic_supervisor = instance.intern.profile.academic_supervisor
            Notification.objects.create(
                recipient=academic_supervisor,
                message=f"{instance.intern.get_full_name()}'s Week {instance.week_number} log has been reviewed and is ready for scoring.",
                notification_type= "LOG_REVIEWED"
            )

#APPROVED notify the student
@receiver(post_save, sender=WeeklyLog)
def notify_on_approved(sender, instance, created, **kwargs):
    if instance.status == "APPROVED":
        old_status = getattr(instance, "_old_status", None)
        if old_status != "APPROVED":
            Notification.objects.create(
                recipient=instance.intern,
                message=f"Your Week {instance.week.number} log has been approved and scored.",
                notification_type= "LOG_APPROVED",
            )

@receiver(post_save, sender=WeeklyLog)
def notify_on_sent_back(sender, instance, created, **kwargs):
    if instance.status == "DRAFT":
        old_status = getattr(instance, "_old_status", None)
        if old_status == "SUBMITTED":
            comment = get_latest_sendback_comment(instance)
            Notification.objeccts.create(
                recipient=instance.intern,
                message=f"Your Week {instance.week_number} log was sent back for revision. Reason: {comment}",
                notification_type="LOG_SENT_BACK",
            )