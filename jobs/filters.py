from django_filters.rest_framework import FilterSet, NumberFilter, BooleanFilter, CharFilter
from jobs.models import Job


class JobFilter(FilterSet):
    employer_id = NumberFilter(field_name='employer__id')
    employer = NumberFilter(field_name='employer__id')
    featured = BooleanFilter(field_name='is_featured')
    is_featured = BooleanFilter(field_name='is_featured')
    category = NumberFilter(field_name='category__id')
    employment_type = CharFilter(field_name='employment_type', lookup_expr='iexact')
    experience_level = CharFilter(field_name='experience_level', lookup_expr='iexact')
    remote_option = CharFilter(field_name='remote_option', lookup_expr='iexact')

    class Meta:
        model = Job
        fields = {
            'category_id': ['exact'],
            'salary': ['gt', 'lt', 'gte', 'lte'],
            'is_featured': ['exact'],
        }