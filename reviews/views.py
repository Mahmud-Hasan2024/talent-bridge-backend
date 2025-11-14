from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from reviews.models import EmployerReview
from reviews.serializers import EmployerReviewSerializer
from reviews.permissions import CanReviewAcceptedJob
from jobs.models import Job
from drf_yasg.utils import swagger_auto_schema

class EmployerReviewViewSet(ModelViewSet):
    """
    Reviews for an employer/job. Expects `job_pk` from nested route.
    """
    serializer_class = EmployerReviewSerializer
    permission_classes = [IsAuthenticated, CanReviewAcceptedJob]

    def get_queryset(self):
        # Avoid running when drf_yasg generates schema
        if getattr(self, "swagger_fake_view", False):
            return EmployerReview.objects.none()

        job_id = self.kwargs.get("job_pk")
        if not job_id:
            return EmployerReview.objects.none()
        return EmployerReview.objects.filter(job_id=job_id)

    @swagger_auto_schema(
        operation_summary="Create an employer review",
        operation_description="Create a review for a job/employer. `job_pk` must be provided in URL.",
        responses={201: EmployerReviewSerializer()}
    )
    def perform_create(self, serializer):
        if getattr(self, "swagger_fake_view", False):
            return

        job_id = self.kwargs.get("job_pk")
        if not job_id:
            raise PermissionDenied("Missing job id in URL.")

        job = Job.objects.get(pk=job_id)

        # Prevent employers from reviewing their own postings
        if job.employer == self.request.user:
            raise PermissionDenied("Employers cannot review their own job postings.")

        serializer.save(job=job, employer=job.employer, job_seeker=self.request.user)

    def perform_update(self, serializer):
        review = self.get_object()
        # Only the job seeker who wrote the review can update it.
        if review.job_seeker != self.request.user:
            raise PermissionDenied("You can only edit your own review.")
            
        serializer.save()

    def perform_destroy(self, instance):
        # Only the job seeker who wrote the review can delete it.
        if instance.job_seeker != self.request.user:
            raise PermissionDenied("You can only delete your own review.")
            
        instance.delete()

    def get_serializer_context(self):
        context = super().get_serializer_context()
        # don't error during swagger schema generation
        if not getattr(self, "swagger_fake_view", False):
            context["job_id"] = self.kwargs.get("job_pk")
        return context
