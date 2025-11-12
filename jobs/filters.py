from django_filters.rest_framework import FilterSet, NumberFilter
from jobs.models import Job


class JobFilter(FilterSet):
    employer_id = NumberFilter(field_name='employer__id')

    class Meta:
        model = Job
        fields = {
            'category_id': ['exact'],
            'salary': ['gt', 'lt']
        }