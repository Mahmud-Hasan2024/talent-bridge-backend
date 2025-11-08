from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from datetime import timedelta
from rest_framework.exceptions import PermissionDenied
from jobs.models import Job
from applications.models import Application
from accounts.models import User
from dashboard.serializers import AdminDashboardSerializer, EmployerDashboardSerializer, SeekerDashboardSerializer
from rest_framework.decorators import action

class DashboardViewSet(ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """Return dashboard summary based on user role"""
        user = request.user
        if getattr(user, "role", None) == "admin":
            return self.admin_dashboard(request)
        elif getattr(user, "role", None) == "employer":
            return self.employer_dashboard(request)
        elif getattr(user, "role", None) == "seeker":
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

        # Top 5 jobs by views
        top_jobs = list(
            jobs_qs.order_by('-views_count')[:5]
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
            Application.objects.filter(applicant=user).order_by('-applied_at')[:5].values('id', 'job_id', 'applied_at', 'status')
        )

        # simple recommendation: jobs not applied to, limit 5
        recommended_jobs = list(
            Job.objects.exclude(applications__applicant=user).filter(is_active=True).order_by('-created_at')[:5]
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

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Return activity stats for dashboard"""
        user = request.user
        days = int(request.query_params.get('days', '7'))
        since = timezone.now() - timedelta(days=days)

        if getattr(user, "role", None) == "admin":
            jobs_created = Job.objects.filter(created_at__gte=since).count()
            applications_created = Application.objects.filter(applied_at__gte=since).count()
        elif getattr(user, "role", None) == "employer":
            jobs_created = Job.objects.filter(employer=user).count()  # all-time for employer
            applications_created = Application.objects.filter(job__in=Job.objects.filter(employer=user)).count()
        elif getattr(user, "role", None) == "seeker":
            jobs_created = 0  # seekers don't create jobs
            applications_created = Application.objects.filter(applicant=user, applied_at__gte=since).count()
        else:
            raise PermissionDenied("Invalid user role for dashboard stats.")

        return Response({
            'days': days,
            'jobs_created': jobs_created,
            'applications_created': applications_created
        })
