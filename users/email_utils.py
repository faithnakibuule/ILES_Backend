# users/email_utils.py
# Uses Django's built-in send_mail via Brevo SMTP relay
# Brevo's relay runs on smtp-relay.brevo.com:587
# Unlike Gmail's SMTP, Brevo's relay is NOT blocked by Render's free tier

from django.conf import settings
from django.core.mail import send_mail
import logging

logger = logging.getLogger(__name__)


def _send(subject, message, recipient_email):
    """
    Private helper — all emails go through here.
    Brevo SMTP relay handles delivery to any recipient
    without domain verification requirements.
    """
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            fail_silently=False,
        )
        logger.info("Email sent successfully to %s", recipient_email)
        return True
    except Exception:
        logger.exception("Error sending email to %s", recipient_email)
        return False


def send_password_reset_email(user, reset_url):
    return _send(
        subject="[ILES] Password reset request",
        message=(
            f"Hello {user.get_full_name() or user.email},\n\n"
            "We received a request to reset your ILES password.\n\n"
            f"Use the link below to set a new password:\n{reset_url}\n\n"
            "If you did not request this change, you can ignore this email.\n\n"
            "Best regards,\n"
            "ILES Team"
        ),
        recipient_email=user.email,
    )


def send_log_submitted_email(student, supervisor, week_number):
    _send(
        subject=f"[ILES] New Log submitted - week {week_number}",
        message=(
            f"Hello {supervisor.first_name},\n\n"
            f"A new weekly log has been submitted by {student.first_name} "
            f"{student.last_name} for week {week_number}.\n\n"
            "Please review the log at your earliest convenience.\n\n"
            "Best regards,\n"
            "ILES Team"
        ),
        recipient_email=supervisor.email,
    )


def send_log_reviewed_email(student, academic_supervisor, week_number):
    _send(
        subject=f"[ILES] Log ready for scoring - Week {week_number}",
        message=(
            f"Hello {academic_supervisor.first_name},\n\n"
            f"A week {week_number} log from {student.first_name} {student.last_name} "
            f"has been reviewed and is ready for scoring.\n\n"
            "Please log in to the ILES system to score the log.\n\n"
            "Best regards,\n"
            "ILES Team"
        ),
        recipient_email=academic_supervisor.email,
    )


def send_log_sent_back_email(student, week_number, comment):
    _send(
        subject=f"[ILES] Your week {week_number} Log Needs Revision",
        message=(
            f"Hello {student.first_name},\n\n"
            f"Your week {week_number} log has been sent back by your workplace "
            f"supervisor with the following comment:\n\n"
            f"Supervisor's comment:\n{comment}\n\n"
            "Please log in to the ILES system to review the comment and resubmit "
            "your log after making the necessary revisions.\n\n"
            "Best regards,\n"
            "ILES Team"
        ),
        recipient_email=student.email,
    )


def send_log_approved_email(student, week_number, score):
    _send(
        subject=f"[ILES] Week {week_number} Log Approved!",
        message=(
            f"Hello {student.first_name},\n\n"
            f"Great news! Your week {week_number} log has been approved with a "
            f"score of {score}.\n\n"
            "Log in to the ILES system to view your score and feedback.\n\n"
            "Best regards,\n"
            "ILES Team"
        ),
        recipient_email=student.email,
    )