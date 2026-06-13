# users/email_utils.py
# Email sending with graceful fallback for Render's free tier

from django.conf import settings
from django.core.mail import send_mail
import logging

logger = logging.getLogger(__name__)


def _send(subject, message, recipient_email):
    """
    Private helper - all emails go through here.
    On Render's free tier SMTP is blocked, so this logs and fails silently.
    """
    logger.info("EMAIL ATTEMPT | To: %s | Subject: %s", recipient_email, subject)

    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            fail_silently=False,
        )
        logger.info("EMAIL SENT | To: %s", recipient_email)
        return True
    except Exception as e:
        logger.warning(
            "EMAIL BLOCKED (Render free tier SMTP restriction) | "
            "To: %s | Subject: %s | Body: %s | Error: %s",
            recipient_email,
            subject,
            message[:200],
            str(e),
        )
        return False


def _get_admin_users():
    from .models import CustomUser

    return CustomUser.objects.filter(role="admin", is_active=True)


def _notify_admins(subject, message):
    for admin in _get_admin_users():
        _send(subject=subject, message=message, recipient_email=admin.email)


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
    supervisor_subject = f"[ILES] New Log submitted - week {week_number}"
    supervisor_message = (
        f"Hello {supervisor.first_name or supervisor.get_full_name() or supervisor.email},\n\n"
        f"A new weekly log has been submitted by {student.first_name} {student.last_name} "
        f"for week {week_number}.\n\n"
        "Please review the log at your earliest convenience.\n\n"
        "Best regards,\n"
        "ILES Team"
    )
    student_subject = f"[ILES] Your Week {week_number} Log was submitted"
    student_message = (
        f"Hello {student.first_name or student.get_full_name() or student.email},\n\n"
        f"Your week {week_number} log has been submitted successfully.\n\n"
        "Your workplace supervisor has been notified.\n\n"
        "Best regards,\n"
        "ILES Team"
    )
    _send(subject=supervisor_subject, message=supervisor_message, recipient_email=supervisor.email)
    _send(subject=student_subject, message=student_message, recipient_email=student.email)
    _notify_admins(
        subject=f"[ILES] New Log submitted - week {week_number}",
        message=(
            f"Hello Admin,\n\n"
            f"{student.first_name} {student.last_name} submitted week {week_number}.\n\n"
            "The workplace supervisor has been notified.\n\n"
            "Best regards,\n"
            "ILES Team"
        ),
    )


def send_log_reviewed_email(student, workplace_supervisor, academic_supervisor, week_number):
    student_subject = f"[ILES] Week {week_number} Log reviewed by your workplace supervisor"
    student_message = (
        f"Hello {student.first_name or student.get_full_name() or student.email},\n\n"
        f"Your week {week_number} log has been reviewed by your workplace supervisor.\n\n"
        "It is now ready for academic scoring.\n\n"
        "Best regards,\n"
        "ILES Team"
    )
    supervisor_subject = f"[ILES] Week {week_number} Log review completed"
    supervisor_message = (
        f"Hello {workplace_supervisor.first_name or workplace_supervisor.get_full_name() or workplace_supervisor.email},\n\n"
        f"You have reviewed week {week_number} of {student.first_name} {student.last_name}'s log.\n\n"
        "The log has been forwarded to the academic supervisor for scoring.\n\n"
        "Best regards,\n"
        "ILES Team"
    )
    academic_subject = f"[ILES] Log ready for scoring - Week {week_number}"
    academic_message = (
        f"Hello {academic_supervisor.first_name or academic_supervisor.get_full_name() or academic_supervisor.email},\n\n"
        f"A week {week_number} log from {student.first_name} {student.last_name} has been reviewed and is ready for scoring.\n\n"
        "Please log in to the ILES system to score the log.\n\n"
        "Best regards,\n"
        "ILES Team"
    )
    _send(subject=student_subject, message=student_message, recipient_email=student.email)
    if workplace_supervisor:
        _send(subject=supervisor_subject, message=supervisor_message, recipient_email=workplace_supervisor.email)
    if academic_supervisor:
        _send(subject=academic_subject, message=academic_message, recipient_email=academic_supervisor.email)
    _notify_admins(
        subject=f"[ILES] Log ready for scoring - Week {week_number}",
        message=(
            f"Hello Admin,\n\n"
            f"Week {week_number} log from {student.first_name} {student.last_name} "
            "is ready for scoring.\n\n"
            "Best regards,\n"
            "ILES Team"
        ),
    )


def send_log_sent_back_email(student, supervisor, week_number, comment):
    if supervisor:
        _send(
            subject=f"[ILES] Your week {week_number} Log Needs Revision",
            message=(
                f"Hello {supervisor.first_name or supervisor.get_full_name() or supervisor.email},\n\n"
                f"The week {week_number} log for {student.first_name} {student.last_name} "
                "has been sent back by the workplace supervisor.\n\n"
                f"Supervisor's comment:\n{comment}\n\n"
                "Best regards,\n"
                "ILES Team"
            ),
            recipient_email=supervisor.email,
        )
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
    _notify_admins(
        subject=f"[ILES] Log sent back - Week {week_number}",
        message=(
            f"Hello Admin,\n\n"
            f"Week {week_number} log for {student.first_name} {student.last_name} "
            f"was sent back by the workplace supervisor.\n\n"
            f"Comment: {comment}\n\n"
            "Best regards,\n"
            "ILES Team"
        ),
    )


def send_log_approved_email(student, academic_supervisor, week_number, score):
    student_subject = f"[ILES] Week {week_number} Log Approved!"
    student_message = (
        f"Hello {student.first_name or student.get_full_name() or student.email},\n\n"
        f"Great news! Your week {week_number} log has been approved with a score of {score}.\n\n"
        "Log in to the ILES system to view your score and feedback.\n\n"
        "Best regards,\n"
        "ILES Team"
    )
    academic_subject = f"[ILES] Week {week_number} evaluation completed"
    academic_message = (
        f"Hello {academic_supervisor.first_name or academic_supervisor.get_full_name() or academic_supervisor.email},\n\n"
        f"You have completed the evaluation for week {week_number} of {student.first_name} {student.last_name}.\n\n"
        f"Final score: {score}.\n\n"
        "Best regards,\n"
        "ILES Team"
    )
    admin_subject = f"[ILES] Student log approved - Week {week_number}"
    admin_message = (
        f"Hello Admin,\n\n"
        f"Week {week_number} log for {student.first_name} {student.last_name} has been approved by the academic supervisor.\n\n"
        f"Final score: {score}.\n\n"
        "Best regards,\n"
        "ILES Team"
    )
    _send(subject=student_subject, message=student_message, recipient_email=student.email)
    if academic_supervisor:
        _send(subject=academic_subject, message=academic_message, recipient_email=academic_supervisor.email)
    _notify_admins(admin_subject, admin_message)
