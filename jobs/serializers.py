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
    employer_name = serializers.ReadOnlyField(source='employer.get_full_name')
    
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=JobCategory.objects.all(),
        source='category',
        write_only=True
    )

    class Meta:
        model = Job
        fields = [
            'id', 'employer', 'employer_name', 'title', 'company_name', 
            'description', 'requirements', 'location', 'category', 
            'category_id', 'is_featured', 'is_active', 'created_at', 
            'employment_type', 'experience_level', 'remote_option', 'salary'
        ]
        read_only_fields = ['id', 'created_at', 'employer_name']

    def update(self, instance, validated_data):
        request = self.context.get('request')
        user_role = getattr(request.user, 'role', '').lower()
        if request and user_role != 'admin':
            validated_data.pop('is_active', None)
            validated_data.pop('is_featured', None)
        return super().update(instance, validated_data)

class SimpleJobDetailSerializer(serializers.ModelSerializer):
    """Serializer used for nesting inside ApplicationSerializer."""
    employer_name = serializers.ReadOnlyField(source='employer.get_full_name')
    
    class Meta:
        model = Job
        fields = (
            'id', 'title', 'company_name', 'employer_name', 'location', 'employment_type', 'remote_option'
        )