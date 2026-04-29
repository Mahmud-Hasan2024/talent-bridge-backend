from django.forms import ValidationError
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from applications.models import Application
from applications.serializers import ApplicationSerializer
from applications.permissions import IsJobSeekerOrReadOnly
from jobs.models import Job
from drf_yasg.utils import swagger_auto_schema

class ApplicationViewSet(ModelViewSet):
    """
    ViewSet for applications.
    - Job seekers see only their own applications.
    - Employers see applications to their own jobs.
    - Admins see everything.
    """
    serializer_class = ApplicationSerializer
    permission_classes = [IsAuthenticated, IsJobSeekerOrReadOnly]

    # 💡 OPTIMIZATION 1: Global Ordering
    # Adding a default ordering ensures consistent results and prevents database 
    # sequence issues when grouping on the frontend.
    ordering = ['-applied_at']

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Application.objects.none()

        user = self.request.user
        
        # 💡 OPTIMIZATION 2: Eager Loading (SQL JOINs)
        # Using select_related here joins the Applicant, Job, and Employer tables.
        # This solves the N+1 problem, meaning for 100 applications, 
        # we do 1 query instead of 301 queries.
        queryset = Application.objects.select_related(
            'applicant', 
            'job', 
            'job__employer'
        )

        if not user.is_authenticated:
            return Application.objects.none()

        user_role = getattr(user, "role", "").lower()

        # 💡 OPTIMIZATION 3: Role-based filtering logic
        # We handle the primary security filter first.
        if user_role == "seeker":
            queryset = queryset.filter(applicant=user)
        elif user_role == "employer":
            queryset = queryset.filter(job__employer=user)
        elif user_role == "admin":
            pass # Admins see all
        else:
            return Application.objects.none()

        # 💡 OPTIMIZATION 4: Streamlined Parameter Filtering
        # Using dictionary unpacking for filters to keep it readable and dry.
        filters = {}
        
        job_employer_id = self.request.query_params.get('job__employer')
        if job_employer_id and (user_role == "admin" or str(user.id) == job_employer_id):
            filters['job__employer_id'] = job_employer_id
        
        applicant_id = self.request.query_params.get('applicant')
        if applicant_id and (user_role == "admin" or str(user.id) == applicant_id):
            filters['applicant_id'] = applicant_id

        return queryset.filter(**filters)

    # 💡 OPTIMIZATION 5: Pagination Bypass
    # When the frontend requests 'no_pagination=true', we return the full list.
    # This is required for your nested grouping (Company > Job > Applicants) to work.
    def paginate_queryset(self, queryset):
        if 'no_pagination' in self.request.query_params:
            return None
        return super().paginate_queryset(queryset)

    def perform_create(self, serializer):
        job_id = self.kwargs.get("job_pk")
        user = self.request.user
        user_role = getattr(user, "role", "").lower()

        if user_role != "seeker":
            raise PermissionDenied("Only job seekers can apply for jobs.")

        if not job_id:
            raise ValidationError("Missing job id in URL.")

        # 💡 OPTIMIZATION 6: Minimal Query Check
        # .exists() is faster than fetching the whole object to check existence.
        if Application.objects.filter(job_id=job_id, applicant=user).exists():
            raise ValidationError("You have already applied for this job.")

        # Using job_id=job_id directly avoids an extra 'Job.objects.get' query.
        serializer.save(job_id=job_id, applicant=user)

    @swagger_auto_schema(operation_summary="Update an application (status)")
    def perform_update(self, serializer):
        user = self.request.user
        application = self.get_object()
        user_role = getattr(user, "role", "").lower()

        # Security check
        if user_role == "employer" and application.job.employer != user:
            raise PermissionDenied("You can only update applications for your own jobs.")
        elif user_role not in ["employer", "admin"]:
            raise PermissionDenied("Only employers or admins can update application status.")
        
        serializer.save()

    @swagger_auto_schema(
        operation_summary="Check if user can review this job",
        operation_description="Returns true if seeker has an 'accepted' application.",
    )
    @action(detail=False, methods=["get"], url_path="can-review/(?P<job_id>[^/.]+)")
    def can_review(self, request, job_id=None):
        user = request.user
        if not user.is_authenticated or getattr(user, "role", "").lower() != "seeker":
            return Response({"can_review": False})

        # Logic remains the same, leveraging DB indices
        can_review = Application.objects.filter(
            job_id=job_id,
            applicant=user,
            status="accepted" # Ensure this matches your model's constant
        ).exists()

        return Response({"can_review": can_review})

    @action(detail=False, methods=["get"], url_path="status-choices")
    def status_choices(self, request):
        choices = [
            {"value": value, "label": display_name}
            for value, display_name in Application.STATUS_CHOICES
        ]
        return Response(choices)

    @action(detail=True, methods=["post"])
    def withdraw(self, request, pk=None, job_pk=None):
        user = request.user
        application = self.get_object()
        user_role = getattr(user, "role", "").lower()

        if user_role != "seeker" or application.applicant != user:
            return Response({"detail": "You can only withdraw your own applications."}, status=403)

        if application.status in ["accepted", "rejected", "withdrawn"]:
            return Response({"detail": f"Cannot withdraw application with status '{application.status}'."}, status=400)

        application.status = "withdrawn"
        application.save()
        return Response({"detail": "Application successfully withdrawn."})