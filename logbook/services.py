# logbook/services.py


def can_transition(log, new_status, user_role):
    """
    Bouncer function — checks if a state transition is allowed.
    Returns True if allowed, False if not.
    """

    if user_role == 'student':
        if log.status == 'DRAFT' and new_status == 'SUBMITTED':
            return True

    elif user_role == 'workplace_supervisor':
        if log.status == 'SUBMITTED' and new_status == 'REVIEWED':
            return True

    elif user_role == 'academic_supervisor':
        if log.status == 'REVIEWED' and new_status == 'APPROVED':
            return True

    return False  # anything else is not allowed