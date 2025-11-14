from rest_framework import serializers
from reviews.models import EmployerReview
from accounts.serializers import SimpleUserDetailSerializer

class EmployerReviewSerializer(serializers.ModelSerializer):
    job_seeker = SimpleUserDetailSerializer(read_only=True)
    employer = SimpleUserDetailSerializer(read_only=True)

    class Meta:
        model = EmployerReview
        fields = [
            'id', 'job', 'job_seeker', 'employer',
            'rating', 'comment', 'created_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'job', 'job_seeker', 'employer',
            'created_at', 'updated_at'
        ]