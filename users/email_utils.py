from django.core.mail import send_mail
from django.conf import settings

def _send(subject, message, recipient_email):
    """
    Private helper — all emails go through here.
    Using a helper means we only change the from_email in one place.
    """
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient_email],
            fail_silently=False,  # raise an exception if the email fails to send
        )
    except Exception as e:
        # Log the error or handle it as needed
        print(f"Error sending email to {recipient_email}: {e}")
        

def send_log_submitted_email(student, supervisor, week_number):
    """
    Fired when: student submits a weekly log
    Sent to: workplace supervisor
    """
    _send(
        subject=f"[ILES] New Log submitted - week {week_number}",
        message = (
            f"Hello {supervisor.first_name},\n\n"
            f"A new weekly log has been submitted by {student.first_name} {student.last_name} for week {week_number}.\n\n"
            f"Please review the log at your earliest convenience.\n\n"
            f"Best regards,\n"
            f"ILES Team"
        ),
        recipient_email=supervisor.email
    )
    
def send_log_reviewed_email(student, academic_supervisor, week_number):
    """
    Fired when: workplace supervisor approves a log (SUBMITTED → REVIEWED)
    Sent to: academic supervisor
    """
    subject = f"[Iles] Log raedy for scoring - Week {week_number}",
    message = (
        f"Hello {academic_supervisor.first_name},\n\n"
        f"A week {week_number} log from {student.firstname} {student.lastname}"
        f"has been reviewed and is ready for scoring.\n\n"
        f"Please log in to the ILES system to review and score the log at your earliest convenience.\n\n"
        f"Best regards,\n"
        f"ILES Team"
    ),
    recipient_email = academic_supervisor.email
    

def send_log_sent_back_email(student, week_number, comment):
    """
    Fired when: workplace supervisor sends a log back to the student
    Sent to: student
    """
    _send(
        subject = f"[ILES] Your week {week_number} Log  Needs Revision ",
        message=(
            f"Hello {student.firstname}\n\n"
            f"Your week {week_number} log has been sent back by your workplace supervisor with the following comment:\n\n"
            f"Supervisor's comment:\n {comment}\n\n"
            
            f"Please log in to the ILES system to review the comment and resubmit your log after making the necessary revisions.\n\n"
            f"Best regards,\n"
            f"ILES Team"
        ),
        recipient_email=student.email
    )
    
def send_log_approved_email(student, week_number , score):
    """
    Fired when: academic supervisor scores and approves a log
    Sent to: student
    """
    _send(
        subject = f"[ILES] Week {week_number} Log Approved!",
        message = (
            f"Hello {student.firstname},\n\n"
            f"Great news! Your week {week_number} log has been approved by your academic supervisor with a score of {score}.\n\n"
            f"Log in to the ILES system to view your score and feedback.\n\n"
            f"Best regards,\n"
            f"ILES Team"
        ),
        recipient_email=student.email
    )
    