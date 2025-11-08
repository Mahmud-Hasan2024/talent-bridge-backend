from rest_framework import serializers

class AdminDashboardSerializer(serializers.Serializer):
    total_users = serializers.IntegerField()
    total_jobs = serializers.IntegerField()
    total_applications = serializers.IntegerField()
    # total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    recent_jobs = serializers.ListField(child=serializers.DictField(), required=False)
    recent_applications = serializers.ListField(child=serializers.DictField(), required=False)


class EmployerDashboardSerializer(serializers.Serializer):
    employer_id = serializers.IntegerField()
    jobs_posted = serializers.IntegerField()
    total_applications = serializers.IntegerField()
    featured_jobs = serializers.IntegerField()
    # earnings = serializers.DecimalField(max_digits=12, decimal_places=2)
    top_jobs = serializers.ListField(child=serializers.DictField(), required=False)


class SeekerDashboardSerializer(serializers.Serializer):
    seeker_id = serializers.IntegerField()
    applications_count = serializers.IntegerField()
    interviews = serializers.IntegerField()
    offers = serializers.IntegerField()
    recently_applied = serializers.ListField(child=serializers.DictField(), required=False)
    recommended_jobs = serializers.ListField(child=serializers.DictField(), required=False)