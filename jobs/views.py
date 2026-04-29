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

    FEATURE_JOB_PRICE = 500

    @action(detail=True, methods=['post'], url_path='feature-payment', permission_classes=[IsAuthenticated])
    def initiate_feature_payment(self, request, pk=None):
        job = self.get_object()
        user = request.user
        self.check_object_permissions(request, job)
        
        if job.is_featured:
            return Response({"error": "This job is already featured."}, status=status.HTTP_400_BAD_REQUEST)

        settings = {
                'store_id': main_settings.SSL_STORE_ID,
                'store_pass': main_settings.SSL_STORE_PASS,
                'issandbox': main_settings.SSL_IS_SANDBOX
            }
        
        sslcz = SSLCOMMERZ(settings)
        tran_id = f"JOB_{job.id}_FEATURE" 
        
        post_body = {
            'total_amount': self.FEATURE_JOB_PRICE,
            'currency': "BDT",
            'tran_id': tran_id,
            'success_url': f"{main_settings.BACKEND_URL}/api/v1/jobs/payment/success/",
            'fail_url': f"{main_settings.BACKEND_URL}/api/v1/jobs/payment/fail/",
            'cancel_url': f"{main_settings.BACKEND_URL}/api/v1/jobs/payment/cancel/",
            'emi_option': 0,
            'cus_name': f"{user.first_name} {user.last_name}",
            'cus_email': user.email,
            'cus_phone': getattr(user, 'phone_number', 'N/A'),
            'cus_add1': getattr(user, 'address', 'N/A'),
            'cus_city': "Dhaka",
            'cus_country': "Bangladesh",
            'shipping_method': "NO",
            'product_name': f"Feature Job: {job.title}",
            'product_category': "Service",
            'product_profile': "general"
        }

        response = sslcz.createSession(post_body)
        if response.get("status") == 'SUCCESS':
            return Response({"payment_url": response['GatewayPageURL']})
        
        return Response({"error": "Payment initiation failed", "details": response}, status=status.HTTP_400_BAD_REQUEST)

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

# -----------------------------
# Payment Callbacks (Untouched)
# -----------------------------
def get_job_id_from_tran_id(tran_id):
    if tran_id and tran_id.startswith("JOB_") and "_FEATURE" in tran_id:
        try:
            return int(tran_id.split('_')[1])
        except (ValueError, IndexError):
            return None
    return None

@api_view(['POST'])
@permission_classes([AllowAny])
def feature_payment_success(request):
    tran_id = request.data.get("tran_id")
    job_id = get_job_id_from_tran_id(tran_id)
    if job_id:
        try:
            job = Job.objects.get(id=job_id)
            job.is_featured = True
            job.save()
            return HttpResponseRedirect(f"{main_settings.FRONTEND_URL}/dashboard/jobs/{job_id}/?payment_status=success")
        except Job.DoesNotExist:
            pass
    return HttpResponseRedirect(f"{main_settings.FRONTEND_URL}/dashboard/jobs/?payment_status=error&tran_id={tran_id}")

@api_view(['POST'])
@permission_classes([AllowAny])
def feature_payment_cancel(request):
    tran_id = request.data.get("tran_id")
    job_id = get_job_id_from_tran_id(tran_id)
    redirect_url = f"{main_settings.FRONTEND_URL}/dashboard/jobs/?payment_status=canceled"
    if job_id:
        redirect_url = f"{main_settings.FRONTEND_URL}/dashboard/jobs/{job_id}/?payment_status=canceled"
    return HttpResponseRedirect(redirect_url)

@api_view(['POST'])
@permission_classes([AllowAny])
def feature_payment_fail(request):
    tran_id = request.data.get("tran_id")
    job_id = get_job_id_from_tran_id(tran_id)
    redirect_url = f"{main_settings.FRONTEND_URL}/dashboard/jobs/?payment_status=failed"
    if job_id:
        redirect_url = f"{main_settings.FRONTEND_URL}/dashboard/jobs/{job_id}/?payment_status=failed"
    return HttpResponseRedirect(redirect_url)