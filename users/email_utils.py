# users/email_utils.py
# Uses Resend HTTPS API instead of SMTP
# Render's free tier blocks port 587 (SMTP) but allows port 443 (HTTPS)
# Resend sends via HTTPS — no port restrictions apply

import resend
import logging
from django.conf import settings

logger = logging.getLogger(__name__)

# Initialise Resend with API key from environment
resend.api_key = settings.RESEND_API_KEY


def _send(subject, message, recipient_email):
    """
    Private helper — all emails go through here.
    Sends via Resend HTTPS API instead of Django's SMTP backend.
    """
    try:
        params = {
            "from": settings.DEFAULT_FROM_EMAIL,
            "to": [recipient_email],
            "subject": subject,
            "text": message,  # plain text email
        }
        resend.Emails.send(params)
        logger.info("Email sent to %s", recipient_email)
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
    """Fired when student submits a weekly log — sent to workplace supervisor"""
    _send(
        subject=f"[ILES] New Log submitted - week {week_number}",
        message=(
            f"Hello {supervisor.first_name},\n\n"
            f"A new weekly log has been submitted by {student.first_name} {student.last_name} "
            f"for week {week_number}.\n\n"
            "Please review the log at your earliest convenience.\n\n"
            "Best regards,\n"
            "ILES Team"
        ),
        recipient_email=supervisor.email,
    )


def send_log_reviewed_email(student, academic_supervisor, week_number):
    """Fired when workplace supervisor approves a log — sent to academic supervisor"""
    _send(
        subject=f"[ILES] Log ready for scoring - Week {week_number}",
        message=(
            f"Hello {academic_supervisor.first_name},\n\n"
            f"A week {week_number} log from {student.first_name} {student.last_name} "
            f"has been reviewed and is ready for scoring.\n\n"
            "Please log in to the ILES system to review and score the log.\n\n"
            "Best regards,\n"
            "ILES Team"
        ),
        recipient_email=academic_supervisor.email,
    )


def send_log_sent_back_email(student, week_number, comment):
    """Fired when workplace supervisor sends a log back — sent to student"""
    _send(
        subject=f"[ILES] Your week {week_number} Log Needs Revision",
        message=(
            f"Hello {student.first_name},\n\n"
            f"Your week {week_number} log has been sent back by your workplace supervisor "
            f"with the following comment:\n\n"
            f"Supervisor's comment:\n{comment}\n\n"
            "Please log in to the ILES system to review the comment and resubmit "
            "your log after making the necessary revisions.\n\n"
            "Best regards,\n"
            "ILES Team"
        ),
        recipient_email=student.email,
    )


def send_log_approved_email(student, week_number, score):
    """Fired when academic supervisor scores a log — sent to student"""
    _send(
        subject=f"[ILES] Week {week_number} Log Approved!",
        message=(
            f"Hello {student.first_name},\n\n"
            f"Great news! Your week {week_number} log has been approved by your "
            f"academic supervisor with a score of {score}.\n\n"
            "Log in to the ILES system to view your score and feedback.\n\n"
            "Best regards,\n"
            "ILES Team"
        ),
        recipient_email=student.email,
    )