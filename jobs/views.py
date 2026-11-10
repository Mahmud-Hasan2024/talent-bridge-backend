from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django.db.models import Count, F
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import status

from jobs.models import Job, JobCategory
from jobs.serializers import JobSerializer, JobCategorySerializer
from jobs.filters import JobFilter
from jobs.paginations import DefaultPagination
from jobs.permissions import IsAdminOrOwner, IsAdminOnly
from applications.models import Application


class JobViewSet(ModelViewSet):
    queryset = Job.objects.select_related("category", "employer").all().order_by("-is_featured", "-created_at")
    serializer_class = JobSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = JobFilter
    search_fields = ["title", "company_name", "description", "location"]
    ordering_fields = ["created_at", "company_name", "title", "salary"]
    pagination_class = DefaultPagination

    def get_queryset(self):
        user = self.request.user
        queryset = super().get_queryset()

        # Check ?featured=true explicitly as well
        featured_param = self.request.query_params.get('featured')
        if featured_param and featured_param.lower() == 'true':
            queryset = queryset.filter(is_featured=True)

        if not user.is_authenticated:
            return queryset.filter(is_active=True)

        user_role = getattr(user, 'role', '').lower()
        if user_role == 'admin':
            return queryset

        employer_param = self.request.query_params.get('employer')
        if user_role == 'employer' and employer_param:
            if str(user.id) == str(employer_param):
                return queryset.filter(employer=user)
            return queryset.none()

        return queryset.filter(is_active=True)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        # Increment views_count atomically in DB
        Job.objects.filter(pk=instance.pk).update(views_count=F('views_count') + 1)
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def perform_create(self, serializer):
        serializer.save(employer=self.request.user)

    def paginate_queryset(self, queryset):
        if 'no_pagination' in self.request.query_params:
            return None
        return super().paginate_queryset(queryset)

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [IsAuthenticatedOrReadOnly()]
        if self.action == "has_applied":
            return [IsAuthenticated()]
        return [IsAuthenticated(), IsAdminOrOwner()]

    @action(detail=True, methods=['get'], url_path='has-applied', permission_classes=[IsAuthenticated])
    def has_applied(self, request, pk=None):
        user = request.user
        if not user.is_authenticated or getattr(user, "role", "").lower() != "seeker":
            return Response({"has_applied": False}, status=status.HTTP_200_OK)

        has_applied = Application.objects.filter(job_id=pk, applicant=user).exists()
        return Response({"has_applied": has_applied})


class JobCategoryViewSet(ModelViewSet):
    queryset = JobCategory.objects.annotate(job_count=Count("jobs")).all().order_by("name")
    serializer_class = JobCategorySerializer
    pagination_class = None

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [IsAuthenticatedOrReadOnly()]
        return [IsAuthenticated(), IsAdminOnly()]