from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied
from django.db.models import Count, F
from jobs.models import Job
from applications.models import Application
from accounts.models import User
from dashboard.serializers import AdminDashboardSerializer, EmployerDashboardSerializer, SeekerDashboardSerializer


class DashboardViewSet(ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        """Return dashboard summary based on user role"""
        user = request.user
        role = getattr(user, "role", "").lower()

        if role == "admin":
            return self.admin_dashboard(request)
        elif role == "employer":
            return self.employer_dashboard(request)
        elif role == "seeker":
            return self.seeker_dashboard(request)
        else:
            raise PermissionDenied("Invalid user role for dashboard.")

    # ------------------- ADMIN DASHBOARD -------------------
    def admin_dashboard(self, request):
        total_users = User.objects.count()
        total_jobs = Job.objects.count()
        total_applications = Application.objects.count()

        recent_jobs = list(
            Job.objects.order_by('-created_at')[:5]
            .values('id', 'title', 'company_name', 'created_at')
        )
        recent_applications = list(
            Application.objects.order_by('-applied_at')[:5]
            .values('id', 'job__title', 'applicant_id', 'applied_at', 'status')
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

    # ------------------- EMPLOYER DASHBOARD -------------------

    def employer_dashboard(self, request):
        user = request.user
        if user.role != 'employer':
            raise PermissionDenied("Only employers can view this dashboard.")

        jobs_qs = Job.objects.filter(employer=user)
        jobs_posted = jobs_qs.count()
        total_applications = Application.objects.filter(job__in=jobs_qs).count()
        featured_jobs = jobs_qs.filter(is_featured=True).count()

        # Annotate applications count and handle null views_count
        from django.db.models import Count, Value
        from django.db.models.functions import Coalesce

        top_jobs_qs = jobs_qs.annotate(
            applications_count=Count('applications', distinct=True),
            safe_views_count=Coalesce('views_count', Value(0))
        ).order_by('-safe_views_count')[:5]

        top_jobs = list(top_jobs_qs.values('id', 'title', 'applications_count', 'safe_views_count'))

        # Rename field for serializer
        for job in top_jobs:
            job['views_count'] = job.pop('safe_views_count', 0)

        payload = {
            'employer_id': user.id,
            'jobs_posted': jobs_posted,
            'total_applications': total_applications,
            'featured_jobs': featured_jobs,
            'top_jobs': top_jobs
        }

        serializer = EmployerDashboardSerializer(payload)
        return Response(serializer.data)



    # ------------------- SEEKER DASHBOARD -------------------
    def seeker_dashboard(self, request):
        user = request.user
        applications_count = Application.objects.filter(applicant=user).count()
        interviews = Application.objects.filter(applicant=user, status='interviewed').count()
        offers = Application.objects.filter(applicant=user, status='offered').count()

        recently_applied = list(
            Application.objects.filter(applicant=user)
            .select_related('job')
            .order_by('-applied_at')[:5]
            .values(
                'id',
                'job__id',
                'job__title',
                'job__company_name',
                'job__location',
                'applied_at',
                'status'
            )
        )

        recommended_jobs = list(
            Job.objects.exclude(applications__applicant=user)
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

        serializer = SeekerDashboardSerializer(data=payload)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data)

    # ------------------- DASHBOARD STATS -------------------
    @action(detail=False, methods=['get'])
    def stats(self, request):
        user = request.user
        role = getattr(user, "role", "").lower()

        if role == "admin":
            jobs_created = Job.objects.count()
            applications_created = Application.objects.count()
        elif role == "employer":
            jobs_created = Job.objects.filter(employer=user).count()
            applications_created = Application.objects.filter(job__in=Job.objects.filter(employer=user)).count()
        elif role == "seeker":
            jobs_created = 0
            applications_created = Application.objects.filter(applicant=user).count()
        else:
            raise PermissionDenied("Invalid user role for dashboard stats.")

        return Response({
            'days': "all-time",
            'jobs_created': jobs_created,
            'applications_created': applications_created
        })
