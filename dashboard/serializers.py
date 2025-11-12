from rest_framework import serializers

# Helper Serializer for the items inside the 'top_jobs' list
class TopJobSerializer(serializers.Serializer):
    """
    Serializer for the aggregated data in the 'top_jobs' list.
    """
    id = serializers.IntegerField()
    title = serializers.CharField()
    views_count = serializers.IntegerField()
    live_applications_count = serializers.IntegerField() 

# ----------------------------------------------------
# Main Dashboard Serializers
# ----------------------------------------------------

class AdminDashboardSerializer(serializers.Serializer):
    total_users = serializers.IntegerField()
    total_jobs = serializers.IntegerField()
    total_applications = serializers.IntegerField()
    # total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2, required=False) # Marked as False since not used in view
    recent_jobs = serializers.ListField(child=serializers.DictField(), required=False)
    recent_applications = serializers.ListField(child=serializers.DictField(), required=False)


class EmployerDashboardSerializer(serializers.Serializer):
    employer_id = serializers.IntegerField()
    jobs_posted = serializers.IntegerField()
    total_applications = serializers.IntegerField()
    featured_jobs = serializers.IntegerField()
    # earnings = serializers.DecimalField(max_digits=12, decimal_places=2, required=False) # Marked as False since not used in view
    top_jobs = TopJobSerializer(many=True, required=False)


class SeekerDashboardSerializer(serializers.Serializer):
    seeker_id = serializers.IntegerField()
    applications_count = serializers.IntegerField()
    interviews = serializers.IntegerField()
    offers = serializers.IntegerField()
    recently_applied = serializers.ListField(child=serializers.DictField(), required=False)
    recommended_jobs = serializers.ListField(child=serializers.DictField(), required=False)