from django.http import HttpResponseRedirect
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly, AllowAny
from django.db.models import Count
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.decorators import action, api_view, permission_classes
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

# Create your views here.

# -----------------------------
# Job ViewSet
# -----------------------------

class JobViewSet(ModelViewSet):
    queryset = Job.objects.select_related("category", "employer").all().order_by("-created_at")
    serializer_class = JobSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = JobFilter
    search_fields = ["title", "company_name", "description", "location"]
    ordering_fields = ["created_at", "company_name", "title"]
    pagination_class = DefaultPagination

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()

        if not user.is_authenticated:
            return queryset

        user_role = getattr(user, 'role', '').lower()
        if user_role == 'admin':
            return queryset
        
        employer_param = self.request.query_params.get('employer')
        if user_role == 'employer' and employer_param:
            if str(user.id) == employer_param:
                return queryset.filter(employer=user)
            return queryset.none()

        return queryset

    def paginate_queryset(self, queryset):
        if 'no_pagination' in self.request.query_params:
            return None
        return super().paginate_queryset(queryset)

    def get_permissions(self):
        if self.action in ["list", "retrieve", "has_applied"]:
            return [IsAuthenticatedOrReadOnly()]
        return [IsAuthenticated(), IsAdminOrOwner()]

    @action(detail=True, methods=['get'], url_path='has-applied', permission_classes=[IsAuthenticated])
    def has_applied(self, request, pk=None):
        user = request.user
        if not user.is_authenticated or getattr(user, "role", "").lower() != "seeker":
            return Response({"has_applied": False, "detail": "Authentication required or user is not a Job Seeker."}, status=status.HTTP_403_FORBIDDEN)
        
        if not Application:
            return Response({"detail": "Application model not loaded."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        has_applied = Application.objects.filter(job_id=pk, applicant=user).exists()
        return Response({"has_applied": has_applied})

    # @action(detail=True, methods=['post'], url_path='make-featured', permission_classes=[IsAuthenticated])
    # def make_featured(self, request, pk=None):
    #     """
    #     Directly marks a job as featured without requiring payment.
    #     """
    #     job = self.get_object()
    #     self.check_object_permissions(request, job)
        
    #     if job.is_featured:
    #         return Response({"message": "This job is already featured."}, status=status.HTTP_200_OK)

    #     job.is_featured = True
    #     job.save()
        
    #     return Response({"message": "Job has been successfully featured."}, status=status.HTTP_200_OK)

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