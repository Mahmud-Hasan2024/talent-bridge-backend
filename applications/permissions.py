from rest_framework.permissions import BasePermission, SAFE_METHODS

class IsJobSeekerOrReadOnly(BasePermission):
    """
    Allows read access (SAFE_METHODS) to all.
    Allows write access (POST, PATCH, PUT) to all authenticated users, 
    but relies on has_object_permission for granular control 
    (Job Seekers on their own apps, Employers on their job's apps).
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        user = request.user
        user_role = getattr(user, "role", "").lower()

        # Rule A: Job Seeker can only update/delete their own application (e.g., to withdraw)
        if user_role == "seeker":
            # Check if the user is the applicant
            return obj.applicant == user

        # Rule B: Employer can only update applications for their own jobs
        if user_role == "employer":
            # Check if the user is the employer of the job associated with the application
            return obj.job.employer == user

        # Rule C: Admin can do anything
        if user_role == "admin":
            return True

        # Deny all others
        return False