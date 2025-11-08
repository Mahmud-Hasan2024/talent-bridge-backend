from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticatedOrReadOnly, IsAuthenticated
from django.db.models import Count
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from jobs.models import Job, JobCategory
from jobs.serializers import JobSerializer, JobCategorySerializer
from jobs.filters import JobFilter
from jobs.paginations import DefaultPagination
from jobs.permissions import IsAdminOrEmployerOrReadOnly


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
        return [IsAuthenticated(), IsAdminOrEmployerOrReadOnly()]

    def get_queryset(self):
        qs = super().get_queryset()
        featured = self.request.query_params.get("featured")
        if featured == "true":
            qs = qs.filter(is_featured=True, is_active=True)

        # Admin can fetch all jobs without pagination
        if getattr(self.request.user, "role", None) == "admin" and self.request.query_params.get("all") == "true":
            self.pagination_class = None

        # Filter by employer if query param present
        employer_id = self.request.query_params.get("employer")
        if employer_id:
            qs = qs.filter(employer_id=employer_id)

        return qs


class JobCategoryViewSet(ModelViewSet):
    queryset = JobCategory.objects.annotate(job_count=Count("jobs")).all()
    serializer_class = JobCategorySerializer
    pagination_class = None

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [IsAuthenticatedOrReadOnly()]
        return [IsAuthenticated(), IsAdminOrEmployerOrReadOnly()]
