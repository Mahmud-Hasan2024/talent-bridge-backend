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

# Create your views here.

class ApplicationViewSet(ModelViewSet):
    """
    ViewSet for applications.
    - Job seekers see only their own applications.
    - Employers see applications to their own jobs.
    - Admins see everything.
    """
    serializer_class = ApplicationSerializer
    permission_classes = [IsAuthenticated, IsJobSeekerOrReadOnly]

    def get_queryset(self):
        # Avoid executing logic during drf_yasg schema generation
        if getattr(self, "swagger_fake_view", False):
            return Application.objects.none()

        user = self.request.user
        queryset = Application.objects.select_related('applicant', 'job', 'job__employer')

        # Safety: if anonymous return empty queryset
        if not user.is_authenticated:
            return Application.objects.none()

        # 💡 FIX 1: Get user role safely and convert to lowercase for case-insensitive check
        user_role = getattr(user, "role", "").lower()

        # 1. Base Queryset Filtered by Role (Security Layer)
        
        # Admin sees everything (no base filter applied)
        if user_role == "admin":
            pass # Keep the full queryset
            
        # Job seekers see only their own applications
        elif user_role == "seeker":
            queryset = queryset.filter(applicant=user)

        # Employers see applications to their own jobs
        elif user_role == "employer":
            # This is the required filter for employers
            queryset = queryset.filter(job__employer=user)
        
        else:
            # Catch-all for unknown roles
            return Application.objects.none()

        
        job_employer_id = self.request.query_params.get('job__employer')
        # 💡 FIX 2: Check query param filtering using the corrected user_role variable
        if job_employer_id and user_role in ["admin", "employer"]:
            if user_role == "admin" or str(user.id) == job_employer_id:
                queryset = queryset.filter(job__employer_id=job_employer_id)
        
        applicant_id = self.request.query_params.get('applicant')
        # 💡 FIX 3: Check query param filtering using the corrected user_role variable
        if applicant_id and user_role in ["admin", "seeker"]:
            if user_role == "admin" or str(user.id) == applicant_id:
                queryset = queryset.filter(applicant_id=applicant_id)

        return queryset

        
    def perform_create(self, serializer):
        # In normal usage job_pk should come from nested URL
        job_id = self.kwargs.get("job_pk")
        user = self.request.user
        
        # 💡 FIX 4: Use case-insensitive role check
        user_role = getattr(user, "role", "").lower()

        if not user.is_authenticated or user_role != "seeker":
            raise PermissionDenied("Only job seekers can apply for jobs.")

        if not job_id:
            raise ValidationError("Missing job id in URL.")

        # Prevent applying twice for the same job
        if Application.objects.filter(job_id=job_id, applicant=user).exists():
            raise ValidationError("You have already applied for this job.")

        job = Job.objects.get(id=job_id)
        serializer.save(job=job, applicant=user)

    @swagger_auto_schema(operation_summary="Update an application (status)")
    def perform_update(self, serializer):
        user = self.request.user
        application = self.get_object()
        
        # 💡 FIX 5: Use case-insensitive role check
        user_role = getattr(user, "role", "").lower()

        if user_role == "employer" and application.job.employer != user:
            raise PermissionDenied("You can only update applications for your own jobs.")
        elif user_role not in ["employer", "admin"]:
            raise PermissionDenied("Only employers or admins can update application status.")
        serializer.save()

    @swagger_auto_schema(
        operation_summary="Withdraw an application",
        operation_description="Job seeker withdraws their own application (if allowed)."
    )
    @action(detail=True, methods=["post"])
    def withdraw(self, request, pk=None, job_pk=None):
        user = request.user
        application = self.get_object()
        
        # 💡 FIX 6: Use case-insensitive role check
        user_role = getattr(user, "role", "").lower()

        if not user.is_authenticated or user_role != "seeker" or application.applicant != user:
            return Response({"detail": "You can only withdraw your own applications."}, status=403)

        if application.status in ["accepted", "rejected", "withdrawn"]:
            return Response({"detail": f"Cannot withdraw application with status '{application.status}'."}, status=400)

        application.status = "withdrawn"
        application.save()
        return Response({"detail": "Application successfully withdrawn."})