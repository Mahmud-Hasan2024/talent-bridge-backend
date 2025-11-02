# dashboard/management/commands/populate_initial_data.py
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group
from django.utils import timezone

from accounts.models import User
from jobs.models import JobCategory, Job
from applications.models import Application
from reviews.models import EmployerReview

from datetime import timedelta
import random

random.seed(42)

def _set_timestamp_if_field_exists(obj, dt):
    """Set timestamp fields like created_at, posted_at, applied_at if they exist."""
    timestamp_fields = [
        "created_at", "created_on", "posted_at", "posted_on",
        "published_at", "date_posted", "applied_at", "applied_on"
    ]
    changed = False
    for fname in timestamp_fields:
        if hasattr(obj, fname):
            try:
                setattr(obj, fname, dt)
                changed = True
            except Exception:
                pass
    if changed:
        try:
            obj.save()
        except Exception:
            pass

class Command(BaseCommand):
    help = "Populate DB with hardcoded Bangladeshi-themed users, jobs, applications, and reviews."

    def handle(self, *args, **kwargs):
        now = timezone.now()

        self.stdout.write("🧹 Deleting old data...")
        Application.objects.all().delete()
        EmployerReview.objects.all().delete()
        Job.objects.all().delete()
        JobCategory.objects.all().delete()
        User.objects.all().delete()
        Group.objects.all().delete()

        # -----------------------
        # GROUPS
        # -----------------------
        admin_group, _ = Group.objects.get_or_create(name="Admin")
        employer_group, _ = Group.objects.get_or_create(name="Employer")
        seeker_group, _ = Group.objects.get_or_create(name="Job Seeker")

        # -----------------------
        # USERS
        # -----------------------
        self.stdout.write("👥 Creating admins...")
        admins_info = [
            ("admin1@dhakajobs.local", "Mahamud", "Hasan", "kgb12345"),
            ("admin2@dhakajobs.local", "Rashedul", "Shohel", "kgb12345"),
            ("admin3@dhakajobs.local", "Fatema", "Khatun", "kgb12345"),
        ]
        admins = []
        for idx, (email, fn, ln, pw) in enumerate(admins_info):
            a = User.objects.create_superuser(email=email, password=pw, first_name=fn, last_name=ln, role="admin")
            a.groups.add(admin_group)
            a.date_joined = now - timedelta(days=180 + idx*30 + random.randint(0,20))
            a.save()
            admins.append(a)

        self.stdout.write("👥 Creating employers...")
        employers_info = [
            ("recruit@dhakatech.com", "Dhaka Tech Ltd", "kgb12345"),
            ("hr@gulshansolutions.com", "Gulshan Solutions", "kgb12345"),
            ("careers@mirpursoft.com", "Mirpur Softworks", "kgb12345"),
            ("talent@chittagongit.com", "Chittagong IT Hub", "kgb12345"),
            ("jobs@rajshahicorp.com", "Rajshahi Corp", "kgb12345"),
            ("hello@sylhetdata.com", "Sylhet Data Labs", "kgb12345"),
            ("contact@banglaads.com", "Bangla Ads", "kgb12345"),
            ("hr@financebd.com", "Finance BD", "kgb12345"),
        ]
        employers = []
        for idx, (email, company, pw) in enumerate(employers_info):
            emp = User.objects.create_user(email=email, password=pw, first_name=company.split()[0], last_name=company.split()[-1], role="employer")
            emp.groups.add(employer_group)
            emp.date_joined = now - timedelta(days=90 + idx*12 + random.randint(0,40))
            emp.save()
            employers.append(emp)

        self.stdout.write("👥 Creating job seekers...")
        seekers_info = [
            ("seeker1@jobportal.local", "Arif", "Haque"),
            ("seeker2@jobportal.local", "Nusrat", "Akter"),
            ("seeker3@jobportal.local", "Tariq", "Islam"),
            ("seeker4@jobportal.local", "Nabila", "Rahman"),
            ("seeker5@jobportal.local", "Sajid", "Khan"),
            ("seeker6@jobportal.local", "Riad", "Siddique"),
            ("seeker7@jobportal.local", "Faria", "Chowdhury"),
            ("seeker8@jobportal.local", "Rakib", "Ahmed"),
            ("seeker9@jobportal.local", "Mita", "Begum"),
            ("seeker10@jobportal.local", "Sourav", "Roy"),
            ("seeker11@jobportal.local", "Meher", "Sultana"),
            ("seeker12@jobportal.local", "Biplob", "Kumar"),
            ("seeker13@jobportal.local", "Jannat", "Parvin"),
            ("seeker14@jobportal.local", "Kamal", "Hossain"),
            ("seeker15@jobportal.local", "Zara", "Islam"),
            ("seeker16@jobportal.local", "Tuhin", "Mia"),
            ("seeker17@jobportal.local", "Simran", "Akhtar"),
            ("seeker18@jobportal.local", "Anik", "Chandra"),
            ("seeker19@jobportal.local", "Lina", "Hasan"),
            ("seeker20@jobportal.local", "Rafi", "Khan"),
            ("seeker21@jobportal.local", "Nazmul", "Sakib"),
            ("seeker22@jobportal.local", "Popy", "Rahman"),
            ("seeker23@jobportal.local", "Ibrahim", "Deb"),
            ("seeker24@jobportal.local", "Polly", "Ahmed"),
            ("seeker25@jobportal.local", "Shamim", "Kibria"),
        ]
        seekers = []
        for idx, (email, fn, ln) in enumerate(seekers_info):
            s = User.objects.create_user(email=email, password="kgb12345", first_name=fn, last_name=ln, role="seeker")
            s.groups.add(seeker_group)
            s.date_joined = now - timedelta(days=5 + (idx*5)%200)
            s.save()
            seekers.append(s)

        # -----------------------
        # JOB CATEGORIES (~15)
        # -----------------------
        self.stdout.write("📂 Creating job categories...")
        categories_info = [
            ("Software Development", "Backend, frontend, full-stack roles."),
            ("Digital Marketing", "SEO, SEM, content marketing, social media."),
            ("Finance & Accounting", "Accounting, auditing, financial analysis."),
            ("Graphic Design", "UI/UX designers, motion graphics, visual artists."),
            ("Data Science", "Data analysis, ML, AI, big data."),
            ("Cybersecurity", "SOC analysts, penetration testers, security engineers."),
            ("Customer Support", "Call center, live chat, customer success."),
            ("Human Resources", "Recruitment, HR operations, talent management."),
            ("Legal", "Corporate, compliance, and legal advisory roles."),
            ("Healthcare", "Nursing, medical technicians, telemedicine."),
            ("Education & Training", "Teachers, trainers, e-learning specialists."),
            ("Logistics & Supply Chain", "Warehouse, shipping, procurement roles."),
            ("Hospitality & Tourism", "Hotels, restaurants, travel agencies."),
            ("Media & Journalism", "Reporters, editors, social media managers."),
            ("Sales & Business Development", "Sales executives, account managers."),
        ]
        categories = {}
        for idx, (name, desc) in enumerate(categories_info):
            c = JobCategory.objects.create(name=name, description=desc)
            _set_timestamp_if_field_exists(c, now - timedelta(days=200 - idx*10))
            categories[name] = c

        # -----------------------
        # JOBS (~55)
        # -----------------------
        self.stdout.write("💼 Creating jobs (~55 jobs)...")
        jobs_data = []
        # Let's generate multiple jobs per employer, multiple categories
        featured_count = 0
        for emp_idx in range(len(employers)):
            for cat_idx, cat_name in enumerate(categories.keys()):
                title = f"{cat_name} Specialist {emp_idx+1}-{cat_idx+1}"
                description = f"Exciting role in {cat_name} at {employers[emp_idx].first_name}."
                requirements = f"Required skills for {cat_name}."
                is_featured = False
                # Make first 10 jobs featured
                if featured_count < 10:
                    is_featured = True
                    featured_count += 1
                employment_type = random.choice(["full_time","part_time","contract"])
                experience_level = random.choice(["entry_level","mid_level","senior_level"])
                remote_option = random.choice(["on_site","remote","hybrid"])
                salary = random.randint(40000,150000)
                jobs_data.append((emp_idx, title, employers[emp_idx].first_name, description, requirements, cat_name, is_featured, employment_type, experience_level, remote_option, salary))
                if len(jobs_data) >= 55:
                    break
            if len(jobs_data) >= 55:
                break

        jobs = []
        for jd in jobs_data:
            (employer_idx, title, company_name, description, requirements,
             category_name, is_featured, employment_type, experience_level,
             remote_option, salary) = jd

            job = Job.objects.create(
                employer=employers[employer_idx],
                title=title,
                company_name=company_name,
                description=description,
                requirements=requirements,
                category=categories[category_name],
                is_featured=is_featured,
                employment_type=employment_type,
                experience_level=experience_level,
                remote_option=remote_option,
                salary=salary
            )
            posted_dt = now - timedelta(days=random.randint(10, 60))
            _set_timestamp_if_field_exists(job, posted_dt)
            jobs.append(job)

        # -----------------------
        # APPLICATIONS
        # -----------------------
        self.stdout.write("✉️ Creating applications...")
        statuses = [Application.PENDING, Application.REVIEWED, Application.INTERVIEWED, Application.OFFERED, Application.ACCEPTED]

        applications = []
        for i, job in enumerate(jobs):
            num_apps = 2 + (i%3)
            base_idx = (i*2)%len(seekers)
            job_posted = getattr(job,"created_at", now - timedelta(days=random.randint(10,60)))
            for j in range(num_apps):
                seeker_obj = seekers[(base_idx+j)%len(seekers)]
                status = statuses[(i+j)%len(statuses)]
                applied_dt = job_posted + timedelta(days=random.randint(3,20))
                if applied_dt > now:
                    applied_dt = now - timedelta(hours=random.randint(1,48))
                resume_path = f"resumes/{seeker_obj.first_name.lower()}_{seeker_obj.last_name.lower()}.pdf"
                app = Application.objects.create(job=job, applicant=seeker_obj, resume=resume_path, status=status)
                _set_timestamp_if_field_exists(app, applied_dt)
                applications.append(app)

        # -----------------------
        # EMPLOYER REVIEWS
        # -----------------------
        self.stdout.write("⭐ Creating employer reviews for accepted applications...")
        for app in applications:
            if app.status == Application.ACCEPTED:
                app_dt = getattr(app, "applied_at", now - timedelta(days=random.randint(1,14)))
                rev_dt = app_dt + timedelta(days=random.randint(1,7))
                if rev_dt > now:
                    rev_dt = now - timedelta(hours=random.randint(1,48))
                rating = 5 if len(app.applicant.first_name)%2 == 0 else 4
                comment = f"{app.applicant.first_name} delivered work for '{app.job.title}'. Recommended."
                review = EmployerReview.objects.create(job=app.job, employer=app.job.employer, job_seeker=app.applicant, rating=rating, comment=comment)
                _set_timestamp_if_field_exists(review, rev_dt)

        self.stdout.write(self.style.SUCCESS("✅ Database populated successfully with 50–60 jobs, multiple categories, and featured jobs!"))
