from django.urls import path, include
from jobs.views import JobViewSet, JobCategoryViewSet
from reviews.views import EmployerReviewViewSet
from applications.views import ApplicationViewSet
from dashboard.views import DashboardViewSet
from rest_framework_nested import routers

router = routers.DefaultRouter()
router.register('jobs', JobViewSet, basename='jobs')
router.register('job-categories', JobCategoryViewSet, basename='job-categories')
router.register('dashboard', DashboardViewSet, basename='dashboard')
router.register('applications', ApplicationViewSet, basename='applications')

# Nested routers for jobs
jobs_router = routers.NestedDefaultRouter(router, 'jobs', lookup='job')
jobs_router.register('reviews', EmployerReviewViewSet, basename='job-reviews')
jobs_router.register('applications', ApplicationViewSet, basename='job-applications')

urlpatterns = [
    path('', include(router.urls)),
    path('', include(jobs_router.urls)),
    path('auth/', include('djoser.urls')),
    path('auth/', include('djoser.urls.jwt')),
]
