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
    


from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAdminOrEmployerOrReadOnly(BasePermission):
    """
    - Admins can do anything.
    - Employers can create/update/delete their own jobs.
    - Safe methods allowed for everyone authenticated.
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return request.user and request.user.is_authenticated

        user = request.user
        return user.is_authenticated and (
            user.groups.filter(name__in=['Admin', 'Employer']).exists()
        )

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        if request.user.groups.filter(name='Admin').exists():
            return True

        if request.user.groups.filter(name='Employer').exists():
            return obj.employer == request.user

        return False



