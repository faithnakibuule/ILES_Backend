# logbook/signals.py

from django.db.models.signals import post_save   # The signal that fires AFTER a model saves
from django.dispatch import receiver              # The decorator that connects function to signal
from .models import WeeklyLog                     # The model we are listening to
from reviews.models import Notification           # The model we are writing to


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