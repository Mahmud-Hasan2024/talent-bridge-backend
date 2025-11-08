from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAdminOrEmployer(BasePermission):
    """Allow Admins and Employers to create/update jobs."""
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        return user.is_authenticated and (
            user.groups.filter(name__in=['Admin', 'Employer']).exists()
        )


class IsAdminOnly(BasePermission):
    """Only Admins can perform certain operations."""
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        return user.is_authenticated and user.groups.filter(name='Admin').exists()
    

class IsAdminOrOwner(BasePermission):
    """
    Allow admin to do anything.
    Allow employer to modify only their own jobs.
    """
    def has_object_permission(self, request, view, obj):
        # Safe methods are always allowed
        if request.method in SAFE_METHODS:
            return True
        # Admin can do anything
        if request.user.groups.filter(name='Admin').exists():
            return True
        # Employer can modify only their jobs
        return obj.employer == request.user

