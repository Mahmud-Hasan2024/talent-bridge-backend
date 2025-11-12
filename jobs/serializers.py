from rest_framework import serializers
from jobs.models import Job, JobCategory

class JobCategorySerializer(serializers.ModelSerializer):
    job_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = JobCategory
        fields = ['id', 'name', 'description', 'job_count']
        read_only_fields = ['id', 'job_count']


class JobSerializer(serializers.ModelSerializer):
    category = JobCategorySerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=JobCategory.objects.all(),
        source='category',
        write_only=True
    )

    class Meta:
        model = Job
        fields = [
            'id', 'employer', 'title', 'company_name', 'description', 'requirements',
            'location', 'category', 'category_id', 'is_featured', 'is_active',
            'created_at', 'employment_type', 'experience_level', 'remote_option', 'salary'
        ]
        read_only_fields = ['id', 'created_at']

    def update(self, instance, validated_data):
        """Only admins can toggle is_active / is_featured."""
        request = self.context.get('request')
        if request and not request.user.groups.filter(name='Admin').exists():
            validated_data.pop('is_active', None)
            validated_data.pop('is_featured', None)
        return super().update(instance, validated_data)
    


class SimpleJobDetailSerializer(serializers.ModelSerializer):
    """Serializer used for nesting inside ApplicationSerializer."""
    # Ensure you include 'company_name' since you rely on it for the Employer column
    class Meta:
        model = Job
        fields = ('id', 'title', 'company_name')
