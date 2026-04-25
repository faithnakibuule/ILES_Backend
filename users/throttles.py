from rest_framework.throttling import AnonRateThrottle

class LoginRateThrottle(AnonRateThrottle):
    """
    Limits the number of login attempts from anonymous users to 5 per minute to
    prevent brute-force attacks.
    """
    scope = 'login'
    
class RegisterRateThrottle(AnonRateThrottle):
    """
    Limits the number of registration attempts from anonymous users to 
    3 per hour per IP address to protect against spam account creation.
    """
    scope = 'register'    