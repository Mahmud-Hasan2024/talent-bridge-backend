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
    serializer_class = JobSerializer
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_class = JobFilter
    search_fields = ["title", "company_name", "description", "location"]
    pagination_class = DefaultPagination
    
    # 💡 OPTIMIZATION 1: Consistent Default Ordering
    ordering = ['-created_at']

    def get_queryset(self):
        user = self.request.user
        
        # 💡 OPTIMIZATION 2: Eager Loading & Field Selection
        # select_related('employer') is crucial if your serializer shows employer names.
        # we add category to prevent N+1 during listing.
        queryset = Job.objects.select_related("category", "employer").all()

        # 💡 OPTIMIZATION 3: Streamlined Role Logic
        if not user.is_authenticated:
            return queryset

        user_role = getattr(user, 'role', '').lower()
        
        # Employer filtering - matches your frontend /jobs/?employer=ID logic
        employer_param = self.request.query_params.get('employer')
        if user_role == 'employer' and employer_param:
            # Security check: Employers should only filter for their own ID
            if str(user.id) == employer_param:
                return queryset.filter(employer=user)
            # If they try to see another employer's ID, we return none or handle as list
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
        
        # 💡 OPTIMIZATION 4: Minimal DB lookup
        # .exists() is significantly faster than any other check.
        exists = Application.objects.filter(job_id=pk, applicant=user).exists()
        return Response({"has_applied": exists})

    @action(detail=True, methods=['post'], url_path='feature-payment')
    def initiate_feature_payment(self, request, pk=None):
        # 💡 OPTIMIZATION 5: Only fetch necessary fields for payment init
        job = self.get_object() 
        self.check_object_permissions(request, job)
        
        # Move SSL logic to a helper or keep minimal
        settings = {
            'store_id': main_settings.SSL_STORE_ID, 
            'store_pass': main_settings.SSL_STORE_PASS, 
            'issandbox': main_settings.SSL_IS_SANDBOX
        }
        sslcz = SSLCOMMERZ(settings)
        
        # Use .get_full_name() for professional payment records
        cus_name = user.get_full_name() if hasattr(user, 'get_full_name') else user.username

        post_body = {
            'total_amount': 500, 'currency': "BDT", 'tran_id': f"JOB_{job.id}_FEATURE",
            'success_url': f"{main_settings.BACKEND_URL}/api/v1/jobs/payment/success/",
            'fail_url': f"{main_settings.BACKEND_URL}/api/v1/jobs/payment/fail/",
            'cancel_url': f"{main_settings.BACKEND_URL}/api/v1/jobs/payment/cancel/",
            'cus_name': cus_name, 'cus_email': request.user.email,
            'cus_phone': 'N/A', 'cus_add1': 'N/A', 'cus_city': "Dhaka", 'cus_country': "Bangladesh",
            'shipping_method': "NO", 'product_name': job.title, 'product_category': "Service", 'product_profile': "general"
        }
        response = sslcz.createSession(post_body)
        
        if response.get("status") == 'SUCCESS':
            return Response({"payment_url": response['GatewayPageURL']})
        return Response({"detail": "Payment session failed"}, status=status.HTTP_400_BAD_REQUEST)
    

# -----------------------------
# JobCategory ViewSet
# -----------------------------


class JobCategoryViewSet(ModelViewSet):
    # 💡 OPTIMIZATION 6: Efficient Counting
    # Prefetch jobs and annotate count in one go.
    queryset = JobCategory.objects.annotate(job_count=Count("jobs"))
    serializer_class = JobCategorySerializer
    pagination_class = None # Fast load for small lists

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