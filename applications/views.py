from rest_framework.exceptions import ValidationError, PermissionDenied
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from applications.models import Application
from applications.serializers import ApplicationSerializer
from applications.permissions import IsJobSeekerOrReadOnly
from drf_yasg.utils import swagger_auto_schema


class ApplicationViewSet(ModelViewSet):
    serializer_class = ApplicationSerializer
    permission_classes = [IsAuthenticated, IsJobSeekerOrReadOnly]
    ordering = ['-applied_at']

    def get_queryset(self):
        if getattr(self, "swagger_fake_view", False):
            return Application.objects.none()

        user = self.request.user
        if not user.is_authenticated:
            return Application.objects.none()

        queryset = Application.objects.select_related(
            'applicant',
            'job',
            'job__employer',
            'job__category',
        ).order_by('-applied_at')

        user_role = getattr(user, "role", "").lower()

        if user_role == "seeker":
            queryset = queryset.filter(applicant=user)
        elif user_role == "employer":
            queryset = queryset.filter(job__employer=user)
        elif user_role == "admin":
            pass
        else:
            return Application.objects.none()

        # Support ?job_pk= (nested route) or ?job= / ?job_id=
        job_pk = self.kwargs.get("job_pk") or self.request.query_params.get("job") or self.request.query_params.get("job_id")
        if job_pk:
            queryset = queryset.filter(job_id=job_pk)

        job_employer_id = self.request.query_params.get('job__employer')
        if job_employer_id and (user_role == "admin" or str(user.id) == str(job_employer_id)):
            queryset = queryset.filter(job__employer_id=job_employer_id)

        applicant_id = self.request.query_params.get('applicant')
        if applicant_id and (user_role == "admin" or str(user.id) == str(applicant_id)):
            queryset = queryset.filter(applicant_id=applicant_id)

        return queryset

    def paginate_queryset(self, queryset):
        if 'no_pagination' in self.request.query_params:
            return None
        return super().paginate_queryset(queryset)

    def perform_create(self, serializer):
        job_id = self.kwargs.get("job_pk") or self.request.data.get("job")
        user = self.request.user
        user_role = getattr(user, "role", "").lower()

        if user_role != "seeker":
            raise PermissionDenied("Only job seekers can apply for jobs.")

        if not job_id:
            raise ValidationError({"detail": "Missing job ID in URL or request body."})

        if Application.objects.filter(job_id=job_id, applicant=user).exists():
            raise ValidationError({"detail": "You have already applied for this job."})

        serializer.save(job_id=job_id, applicant=user)

    @swagger_auto_schema(operation_summary="Update an application (status)")
    def perform_update(self, serializer):
        user = self.request.user
        application = self.get_object()
        user_role = getattr(user, "role", "").lower()

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

        can_review = Application.objects.filter(
            job_id=job_id,
            applicant=user,
            status="accepted"
        ).exists()

        return Response({"can_review": can_review})

    @action(detail=False, methods=["get"], url_path="status-choices")
    def status_choices(self, request):
        choices = [
            {"value": value, "label": display_name}
            for value, display_name in Application.STATUS_CHOICES
        ]
        return Response(choices)

    @action(detail=True, methods=["post", "delete"], url_path="withdraw")
    def withdraw(self, request, pk=None, job_pk=None):
        user = request.user
        application = self.get_object()
        user_role = getattr(user, "role", "").lower()

        if user_role != "seeker" or application.applicant != user:
            return Response({"detail": "You can only withdraw your own applications."}, status=403)

        if application.status in ["accepted", "rejected", "withdrawn"]:
            return Response({"detail": f"Cannot withdraw application with status '{application.status}'."}, status=400)

        application.status = "withdrawn"
        application.save(update_fields=["status"])
        return Response({"detail": "Application successfully withdrawn.", "status": "withdrawn"})