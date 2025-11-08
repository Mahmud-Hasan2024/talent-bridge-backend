from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Sum
from jobs.models import Job
from applications.models import Application
from accounts.models import User
from dashboard.serializers import AdminDashboardSerializer, EmployerDashboardSerializer, SeekerDashboardSerializer
from rest_framework.exceptions import PermissionDenied
from rest_framework.decorators import action
from django.utils import timezone
from datetime import timedelta
from drf_yasg.utils import swagger_auto_schema

class DashboardViewSet(ViewSet):
    permission_classes = [IsAuthenticated]

    @swagger_auto_schema(
        operation_summary="Get dashboard summary for current user",
        operation_description="Returns admin/employer/seeker specific dashboard info based on your role."
    )
    def list(self, request):
        user = request.user
        role = getattr(user, "role", None)

        if role == "admin":
            return self.admin_dashboard(request)
        elif role == "employer":
            return self.employer_dashboard(request)
        elif role == "seeker":
            return self.seeker_dashboard(request)
        else:
            raise PermissionDenied("Invalid user role for dashboard.")

    def admin_dashboard(self, request):
        total_users = User.objects.count()
        total_jobs = Job.objects.count()
        total_applications = Application.objects.count()

        recent_jobs = list(
            Job.objects.order_by('-created_at')[:5].values('id', 'title', 'company_name', 'created_at')
        )
        recent_applications = list(
            Application.objects.order_by('-applied_at')[:5].values('id', 'job_id', 'applicant_id', 'applied_at', 'status')
        )

        payload = {
            'total_users': total_users,
            'total_jobs': total_jobs,
            'total_applications': total_applications,
            'recent_jobs': recent_jobs,
            'recent_applications': recent_applications
        }
        serializer = AdminDashboardSerializer(payload)
        return Response(serializer.data)

    def employer_dashboard(self, request):
        user = request.user
        jobs_qs = Job.objects.filter(employer=user)
        jobs_posted = jobs_qs.count()
        total_applications = Application.objects.filter(job__in=jobs_qs).count()
        featured_jobs = jobs_qs.filter(is_featured=True).count()

        # Count applications for each job
        top_jobs = list(
            jobs_qs.annotate(applications_count=Count('applications'))
            .order_by('-views_count')[:5]
            .values('id', 'title', 'views_count', 'applications_count')
        )

        payload = {
            'employer_id': user.id,
            'jobs_posted': jobs_posted,
            'total_applications': total_applications,
            'featured_jobs': featured_jobs,
            'top_jobs': top_jobs
        }
        serializer = EmployerDashboardSerializer(payload)
        return Response(serializer.data)

    def seeker_dashboard(self, request):
        user = request.user
        applications_count = Application.objects.filter(applicant=user).count()
        interviews = Application.objects.filter(applicant=user, status='interviewed').count()
        offers = Application.objects.filter(applicant=user, status='offered').count()

        recently_applied = list(
            Application.objects.filter(applicant=user).order_by('-applied_at')[:5]
            .values('id', 'job_id', 'applied_at', 'status')
        )

        recommended_jobs = list(
            Job.objects.exclude(applications__applicant=user)
            .filter(is_active=True)
            .order_by('-created_at')[:5]
            .values('id', 'title', 'company_name', 'location')
        )

        payload = {
            'seeker_id': user.id,
            'applications_count': applications_count,
            'interviews': interviews,
            'offers': offers,
            'recently_applied': recently_applied,
            'recommended_jobs': recommended_jobs
        }
        serializer = SeekerDashboardSerializer(payload)
        return Response(serializer.data)

    @swagger_auto_schema(
        operation_summary="Dashboard stats for a number of days",
        operation_description="Example: /dashboard/stats/?days=7"
    )
    @action(detail=False, methods=['get'])
    def stats(self, request):
        days = int(request.query_params.get('days', '7'))
        since = timezone.now() - timedelta(days=days)
        jobs_created = Job.objects.filter(created_at__gte=since).count()
        applications_created = Application.objects.filter(applied_at__gte=since).count()
        return Response({'days': days, 'jobs_created': jobs_created, 'applications_created': applications_created})
