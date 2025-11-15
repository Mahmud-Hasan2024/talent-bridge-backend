from django.db import models
from django.conf import settings
from jobs.models import Job

# Create your models here.

class Application(models.Model):
    PENDING = 'pending'
    REVIEWED = 'reviewed'
    INTERVIEWED = 'interviewed'
    OFFERED = 'offered'
    ACCEPTED = 'accepted'
    REJECTED = 'rejected'
    WITHDRAWN = 'withdrawn'

    STATUS_CHOICES = [
        (PENDING, 'Pending'),
        (REVIEWED, 'Reviewed'),
        (INTERVIEWED, 'Interviewed'),
        (OFFERED, 'Offered'),
        (ACCEPTED, 'Accepted'),
        (REJECTED, 'Rejected'),
        (WITHDRAWN, 'Withdrawn'),
    ]

    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    applicant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='applications')
    resume = models.TextField()
    cover_letter = models.TextField(blank=True, null=True)
    portfolio_link = models.CharField(max_length=255, blank=True, null=True)
    applied_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default=PENDING)

    def __str__(self):
        return f"Application of {self.applicant.email} for {self.job.title}"