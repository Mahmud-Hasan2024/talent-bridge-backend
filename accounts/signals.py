from django.db.models.signals import post_migrate, post_save
from django.contrib.auth.models import Group
from django.dispatch import receiver
from django.contrib.auth import get_user_model

User = get_user_model()

@receiver(post_migrate)
def create_default_groups(sender, **kwargs):
    """Ensure default groups always exist."""
    if not sender.name.endswith("accounts"):
        return

    for group_name in ["Admin", "Employer", "Job Seeker"]:
        Group.objects.get_or_create(name=group_name)


@receiver(post_save, sender=User)
def sync_group_and_role(sender, instance, created, **kwargs):
    """Ensure group and role stay consistent after save."""
    if created:
        instance.sync_group_with_role()
