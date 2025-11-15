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

    FEATURE_JOB_PRICE = 500

    @action(detail=True, methods=['post'], url_path='feature-payment', permission_classes=[IsAuthenticated])
    def initiate_feature_payment(self, request, pk=None):
        """
        Initiates SSLCOMMERZ payment for featuring a specific job.
        Only the Job Owner (Employer) can call this.
        """
        job = self.get_object()
        user = request.user
        
        # 1. Authorization Check (IsAdminOrOwner ensures the owner or admin pays)
        self.check_object_permissions(request, job)
        
        # 2. Prevent payment if already featured
        if job.is_featured:
            return Response({"error": "This job is already featured."}, status=status.HTTP_400_BAD_REQUEST)

        # 3. Setup SSLCOMMERZ
        settings = {
                'store_id': main_settings.SSL_STORE_ID,
                'store_pass': main_settings.SSL_STORE_PASS,
                'issandbox': main_settings.SSL_IS_SANDBOX
            }
        
        sslcz = SSLCOMMERZ(settings)
        
        tran_id = f"JOB_{job.id}_FEATURE" 
        
        post_body = {
            'total_amount': FEATURE_JOB_PRICE,
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
# Payment Callbacks for Featuring Jobs
# -----------------------------

def get_job_id_from_tran_id(tran_id):
    if tran_id and tran_id.startswith("JOB_") and "_FEATURE" in tran_id:
        try:
            # Splits "JOB_123_FEATURE" -> ["JOB", "123", "FEATURE"] -> returns "123"
            return int(tran_id.split('_')[1])
        except (ValueError, IndexError):
            return None
    return None

# --- Payment Success ---
@api_view(['POST'])
@permission_classes([AllowAny])
def feature_payment_success(request):
    tran_id = request.data.get("tran_id")
    job_id = get_job_id_from_tran_id(tran_id)
    
    if job_id:
        try:
            job = Job.objects.get(id=job_id)
            # Update the job field
            job.is_featured = True
            job.save()
            # Redirect to the job dashboard or success page
            return HttpResponseRedirect(f"{main_settings.FRONTEND_URL}/dashboard/jobs/{job_id}/?payment_status=success")
        except Job.DoesNotExist:
            pass # Handle gracefully even if job is not found

    # Fallback redirect
    return HttpResponseRedirect(f"{main_settings.FRONTEND_URL}/dashboard/jobs/?payment_status=error&tran_id={tran_id}")

# --- Payment Cancel ---
@api_view(['POST'])
@permission_classes([AllowAny])
def feature_payment_cancel(request):
    tran_id = request.data.get("tran_id")
    job_id = get_job_id_from_tran_id(tran_id)
    
    # We don't change job status on cancel, but we redirect the user
    redirect_url = f"{main_settings.FRONTEND_URL}/dashboard/jobs/?payment_status=canceled"
    if job_id:
        redirect_url = f"{main_settings.FRONTEND_URL}/dashboard/jobs/{job_id}/?payment_status=canceled"

    return HttpResponseRedirect(redirect_url)

# --- Payment Fail ---
@api_view(['POST'])
@permission_classes([AllowAny])
def feature_payment_fail(request):
    tran_id = request.data.get("tran_id")
    job_id = get_job_id_from_tran_id(tran_id)

    # We don't change job status on fail, but we redirect the user
    redirect_url = f"{main_settings.FRONTEND_URL}/dashboard/jobs/?payment_status=failed"
    if job_id:
        redirect_url = f"{main_settings.FRONTEND_URL}/dashboard/jobs/{job_id}/?payment_status=failed"

    return HttpResponseRedirect(redirect_url)