from django.db.models.signals import post_save
from django.dispatch import receiver
from applications.models import Application
from notifications.models import Notification


@receiver(post_save, sender=Application)
def notify_on_application_change(sender, instance, created, **kwargs):
    if created:
        Notification.objects.create(
            recipient=instance.job.employer,
            title="New Job Application",
            message=f"{instance.applicant.email} applied for '{instance.job.title}'."
        )
    else:
        Notification.objects.create(
            recipient=instance.applicant,
            title="Application Status Updated",
            message=f"Your application for '{instance.job.title}' at {instance.job.company_name} is now '{instance.status.upper()}'."
        )