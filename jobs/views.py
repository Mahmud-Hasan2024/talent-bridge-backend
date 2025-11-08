from jobs.models import Job, JobCategory
from jobs.serializers import JobSerializer, JobCategorySerializer
from django.db.models import Count
from django_filters.rest_framework import DjangoFilterBackend
from jobs.filters import JobFilter
from rest_framework.filters import SearchFilter, OrderingFilter
from jobs.paginations import DefaultPagination
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated, SAFE_METHODS, BasePermission
from drf_yasg.utils import swagger_auto_schema
from jobs.permissions import IsAdminOrEmployer, IsAdminOrOwner


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

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [IsAuthenticatedOrReadOnly()]
        return [IsAuthenticated(), IsAdminOrOwner()]

    def get_queryset(self):
        qs = super().get_queryset()
        featured = self.request.query_params.get("featured")
        if featured == "true":
            qs = qs.filter(is_featured=True, is_active=True)

        # ✅ If admin wants all jobs, disable pagination
        if getattr(self.request.user, "role", None) == "admin" and self.request.query_params.get("all") == "true":
            self.pagination_class = None

        return qs


# -----------------------------
# Job Category ViewSet
# -----------------------------
class JobCategoryViewSet(ModelViewSet):
    queryset = JobCategory.objects.annotate(job_count=Count("jobs")).all()
    serializer_class = JobCategorySerializer
    pagination_class = None  # always show all categories

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [IsAuthenticatedOrReadOnly()]
        return [IsAuthenticated(), IsAdminOrOwner()]

    @swagger_auto_schema(operation_summary="List job categories")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
