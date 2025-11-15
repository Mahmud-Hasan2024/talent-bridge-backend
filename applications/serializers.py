from rest_framework import serializers
from applications.models import Application
from jobs.serializers import SimpleJobDetailSerializer
from accounts.serializers import SimpleUserDetailSerializer

class ApplicationSerializer(serializers.ModelSerializer):
    applicant = SimpleUserDetailSerializer(read_only=True)
    job = SimpleJobDetailSerializer(read_only=True)
    job_employer_name = serializers.CharField(source='job.company_name', read_only=True) 
    
    resume = serializers.FileField(required=True)
    cover_letter = serializers.FileField(required=False, allow_null=True)
    portfolio_link = serializers.URLField(required=False, allow_null=True)
    
    class Meta:
        model = Application
        fields = [ 
            'id', 'cover_letter', 'resume', 'portfolio_link', 
            'applied_at', 'status', 'job_employer_name',
            
            'job', 'applicant' 
        ]
        
        read_only_fields = [
            'id', 'job', 'applicant', 'applied_at', 'status', 'job_employer_name',
        ]