from rest_famework.permissions import BasePermission

class IsStudentUser(BasePermission):
    #Grants access only to the authenticated users with the sers role of 'student'.
    #Used on log submission, my placement, my scores endpoints.
    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and request.user.role == 'student'
        )
    
class IsWorkplaceSupervisor(BasePermission):
    #Grant access only to the authenticated users with the user role of workplace supervisor.
    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and request.user.role == 'workplace_supervisor'
        )
    
class IsAcademicSupervisor(BasePermission):
    #Grant access only to the authenticated users with the user role of academic supervisor.
    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and request.user.role == 'academic_supervisor'
        )
    
class IsAdminUser(BasePermission):
    #Grant access only to the authenticated users with the user role of admin.
    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and request.user.role == 'admin'
        )
    