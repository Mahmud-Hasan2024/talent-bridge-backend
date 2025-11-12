from rest_framework import serializers
from applications.models import Application
from jobs.serializers import SimpleJobDetailSerializer
from accounts.serializers import SimpleUserDetailSerializer

class ApplicationSerializer(serializers.ModelSerializer):
    applicant = SimpleUserDetailSerializer(read_only=True)
    job = SimpleJobDetailSerializer(read_only=True)
    job_employer_name = serializers.CharField(source='job.company_name', read_only=True) 

    class Meta:
        model = Application
        fields = [ 
             'id', 'job', 'applicant', 'cover_letter', 'resume', 
             'portfolio_link', 'applied_at', 'status', 'job_employer_name'
        ]
        
        read_only_fields = ['applied_at', 'status']