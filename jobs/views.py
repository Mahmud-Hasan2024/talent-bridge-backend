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

from sslcommerz_lib import SSLCOMMERZ 
from django.conf import settings as main_settings
from rest_framework import status


# Create your views here.


class JobViewSet(ModelViewSet):
    serializer_class = JobSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = JobFilter
    search_fields = ["title", "company_name", "description", "location"]
    pagination_class = DefaultPagination

    def get_queryset(self):
        user = self.request.user
        
        # 💡 OPTIMIZATION: Eager Loading
        # We join 'category' and 'employer' here. 
        # Since your model HAS 'employer = models.ForeignKey...', this is now safe.
        queryset = Job.objects.select_related("category", "employer").all().order_by("-created_at")

        if not user.is_authenticated:
            return queryset

        user_role = getattr(user, 'role', '').lower()
        
        # Admins see everything
        if user_role == 'admin':
            return queryset
        
        # Employer filtering logic
        employer_param = self.request.query_params.get('employer')
        if user_role == 'employer' and employer_param:
            # Only allow filtering if the ID matches the logged-in user
            if str(user.id) == employer_param:
                return queryset.filter(employer=user)
            return queryset.none()

        return queryset

    def get_permissions(self):
        if self.action in ["list", "retrieve", "has_applied"]:
            return [IsAuthenticatedOrReadOnly()]
        return [IsAuthenticated(), IsAdminOrOwner()]

    def paginate_queryset(self, queryset):
        if 'no_pagination' in self.request.query_params:
            return None
        return super().paginate_queryset(queryset)

    @action(detail=True, methods=['get'], url_path='has-applied')
    def has_applied(self, request, pk=None):
        user = request.user
        if not user.is_authenticated or getattr(user, "role", "").lower() != "seeker":
            return Response({"has_applied": False})
        
        # 💡 OPTIMIZATION: .exists() is faster than .count() or fetching
        has_applied = Application.objects.filter(job_id=pk, applicant=user).exists()
        return Response({"has_applied": has_applied})

    # initiate_feature_payment remains EXACTLY as your original
    @action(detail=True, methods=['post'], url_path='feature-payment')
    def initiate_feature_payment(self, request, pk=None):
        job = self.get_object()
        self.check_object_permissions(request, job)
        
        settings = {'store_id': main_settings.SSL_STORE_ID, 'store_pass': main_settings.SSL_STORE_PASS, 'issandbox': main_settings.SSL_IS_SANDBOX}
        sslcz = SSLCOMMERZ(settings)
        post_body = {
            'total_amount': 500, 'currency': "BDT", 'tran_id': f"JOB_{job.id}_FEATURE",
            'success_url': f"{main_settings.BACKEND_URL}/api/v1/jobs/payment/success/",
            'fail_url': f"{main_settings.BACKEND_URL}/api/v1/jobs/payment/fail/",
            'cancel_url': f"{main_settings.BACKEND_URL}/api/v1/jobs/payment/cancel/",
            'cus_name': f"{request.user.first_name}", 'cus_email': request.user.email,
            'cus_phone': 'N/A', 'cus_add1': 'N/A', 'cus_city': "Dhaka", 'cus_country': "Bangladesh",
            'shipping_method': "NO", 'product_name': job.title, 'product_category': "Service", 'product_profile': "general"
        }
        response = sslcz.createSession(post_body)
        return Response({"payment_url": response['GatewayPageURL']}) if response.get("status") == 'SUCCESS' else Response(status=400)

class JobCategoryViewSet(ModelViewSet):
    # 💡 OPTIMIZATION: One query for name and count
    queryset = JobCategory.objects.annotate(job_count=Count("jobs")).all()
    serializer_class = JobCategorySerializer
    pagination_class = None

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [IsAuthenticatedOrReadOnly()]
        return [IsAuthenticated(), IsAdminOrOwner()]