from django.db import models
from django.contrib.auth.models import AbstractUser, Group
from accounts.managers import CustomUserManager
from cloudinary.models import CloudinaryField

class User(AbstractUser):
    ROLE_ADMIN = 'admin'
    ROLE_EMPLOYER = 'employer'
    ROLE_SEEKER = 'seeker'

    ROLE_CHOICES = [
        (ROLE_ADMIN, 'Admin'),
        (ROLE_EMPLOYER, 'Employer'),
        (ROLE_SEEKER, 'Job Seeker'),
    ]

    username = None
    email = models.EmailField(unique=True)
    bio = models.TextField(blank=True, null=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default=ROLE_SEEKER)
    address = models.CharField(max_length=255, blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    profile_picture = CloudinaryField('profile_pictures', blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    skills = models.TextField(max_length=5000, blank=True, null=True)
    education = models.TextField(max_length=5000, blank=True, null=True)
    experience = models.TextField(max_length=5000, blank=True, null=True)
    linkedin_profile = models.URLField(blank=True, null=True)
    github_profile = models.URLField(blank=True, null=True)
    portfolio_website = models.URLField(blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    objects = CustomUserManager()

    def __str__(self):
        return f"{self.email} ({self.get_role_display()})"

    def save(self, *args, **kwargs):
        """Keep Django groups in sync with role field."""
        super().save(*args, **kwargs)
        self.sync_group_with_role()

    def sync_group_with_role(self):
        """Ensure role and groups are always in sync."""
        group_mapping = {
            'admin': 'Admin',
            'employer': 'Employer',
            'seeker': 'Job Seeker',
        }
        desired_group_name = group_mapping.get(self.role)
        if not desired_group_name:
            return

        # Remove user from all role groups
        self.groups.clear()
        group, _ = Group.objects.get_or_create(name=desired_group_name)
        self.groups.add(group)
