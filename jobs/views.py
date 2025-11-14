from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django.db.models import Count
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status

from jobs.models import Job, JobCategory
from jobs.serializers import JobSerializer, JobCategorySerializer
from jobs.filters import JobFilter
from jobs.paginations import DefaultPagination
from jobs.permissions import IsAdminOrOwner

try:
    from applications.models import Application
except ImportError:
    Application = None


# -----------------------------
# Job ViewSet
# -----------------------------
class JobViewSet(ModelViewSet):
    queryset = Job.objects.select_related("category").all().order_by("-created_at")
    serializer_class = JobSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = JobFilter
    search_fields = ["title", "company_name", "description", "location"]
    ordering_fields = ["created_at", "company_name", "title"]
    pagination_class = DefaultPagination

    def paginate_queryset(self, queryset):
        if 'no_pagination' in self.request.query_params:
            return None
        
        # Otherwise, use the default pagination logic
        return super().paginate_queryset(queryset)

    def get_permissions(self):
        if self.action in ["list", "retrieve", "has_applied"]:
            return [IsAuthenticatedOrReadOnly()]
        return [IsAuthenticated(), IsAdminOrOwner()]

    @action(detail=True, methods=['get'], url_path='has-applied', permission_classes=[IsAuthenticated])
    def has_applied(self, request, pk=None):
        """
        Checks if the current authenticated user (Job Seeker) has an application
        for the job specified by pk.
        """
        user = request.user
        job_id = pk

        if not user.is_authenticated or getattr(user, "role", "").lower() != "seeker":
            return Response({"has_applied": False, "detail": "Authentication required or user is not a Job Seeker."}, status=status.HTTP_403_FORBIDDEN)
        
        if not Application:
            return Response({"detail": "Application model not loaded."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        try:
            has_applied = Application.objects.filter(
                job_id=job_id,
                applicant=user
            ).exists()
            
            return Response({"has_applied": has_applied})
        
        except Exception as e:
            print(f"Error checking application status: {e}")
            return Response({"detail": "An internal error occurred during the check."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# -----------------------------
# JobCategory ViewSet
# -----------------------------
class JobCategoryViewSet(ModelViewSet):
    queryset = JobCategory.objects.annotate(job_count=Count("jobs")).all()
    serializer_class = JobCategorySerializer
    pagination_class = None

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [IsAuthenticatedOrReadOnly()]
        return [IsAuthenticated(), IsAdminOrOwner()]