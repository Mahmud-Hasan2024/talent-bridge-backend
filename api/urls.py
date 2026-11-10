from django.urls import path, include
from rest_framework_nested import routers
from jobs.views import JobViewSet, JobCategoryViewSet
from applications.views import ApplicationViewSet
from reviews.views import EmployerReviewViewSet
from dashboard.views import DashboardViewSet
from notifications.views import NotificationViewSet

router = routers.DefaultRouter()
router.register("jobs", JobViewSet, basename="jobs")
router.register("job-categories", JobCategoryViewSet, basename="job-categories")
router.register("applications", ApplicationViewSet, basename="applications")
router.register("dashboard", DashboardViewSet, basename="dashboard")
router.register("notifications", NotificationViewSet, basename="notifications")

jobs_router = routers.NestedDefaultRouter(router, "jobs", lookup="job")
jobs_router.register("applications", ApplicationViewSet, basename="job-applications")
jobs_router.register("reviews", EmployerReviewViewSet, basename="job-reviews")

urlpatterns = [
    path("", include(router.urls)),
    path("", include(jobs_router.urls)),
    path("auth/", include("djoser.urls")),
    path("auth/", include("djoser.urls.jwt")),
    path("payments/", include("payments.urls")),
]