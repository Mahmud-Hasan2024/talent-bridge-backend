from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsAdminOrEmployer(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        return user.is_authenticated and (
            getattr(user, 'role', '').lower() in ['admin', 'employer']
            or user.groups.filter(name__in=['Admin', 'Employer']).exists()
        )

class IsAdminOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        user = request.user
        return user.is_authenticated and (
            getattr(user, 'role', '').lower() == 'admin'
            or user.is_superuser
            or user.groups.filter(name='Admin').exists()
        )

class IsAdminOrOwner(BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if getattr(request.user, 'role', '').lower() == 'admin' or request.user.is_superuser:
            return True
        return getattr(obj, 'employer', None) == request.user