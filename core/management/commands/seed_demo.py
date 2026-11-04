"""Populate a deterministic ProjectMate demonstration database."""

from datetime import timedelta
from pathlib import Path
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile
from django.utils import timezone
from discovery.models import Category, Skill, UserSkill
from projects.models import Project
from projects.services import sync_project_status
from teams.models import JoinRequest, Membership
from activity.models import ProjectResource


class Command(BaseCommand):
    """Create realistic demo content without duplicate rows."""

    help = "Create or reset ProjectMate demo data."

    def add_arguments(self, parser):
        """Add the optional reset flag."""
        parser.add_argument("--reset", action="store_true", help="Remove demo records before seeding.")

    def handle(self, *args, **options):
        """Seed users, categories, skills, projects, teams, and resources."""
        User = get_user_model()
        if options["reset"]:
            ProjectResource.objects.all().delete()
            JoinRequest.objects.all().delete()
            Membership.objects.all().delete()
            Project.objects.all().delete()
            UserSkill.objects.all().delete()
            Skill.objects.all().delete()
            Category.objects.all().delete()
            User.objects.filter(username__in=["admin", "demo", "owner_demo", "sam_student"]).delete()
        categories = [
            ("Web Development", "web-development", "Web applications and services.", "bi-code-slash"),
            ("Mobile Apps", "mobile-apps", "Mobile experiences for campus life.", "bi-phone"),
            ("AI & Data Science", "ai-data-science", "Data analysis and intelligent systems.", "bi-graph-up"),
            ("Game Development", "game-development", "Games and interactive media.", "bi-controller"),
            ("IoT & Hardware", "iot-hardware", "Connected devices and sensors.", "bi-cpu"),
            ("Research", "research", "Research projects with practical impact.", "bi-journal-text"),
            ("Design & UX", "design-ux", "Human-centred product design.", "bi-palette"),
            ("Cybersecurity", "cybersecurity", "Security education and tooling.", "bi-shield-check"),
        ]
        category_objects = [Category.objects.update_or_create(slug=slug, defaults={"name": name, "description": description, "icon": icon, "sort_order": index})[0] for index, (name, slug, description, icon) in enumerate(categories, 1)]
        skill_names = [("Python", "python", "language"), ("Django", "django", "framework"), ("JavaScript", "javascript", "language"), ("React", "react", "framework"), ("Data analysis", "data-analysis", "data"), ("Figma", "figma", "design"), ("Git", "git", "tools"), ("Technical writing", "technical-writing", "soft"), ("Testing", "testing", "tools"), ("SQL", "sql", "language")]
        skill_objects = [Skill.objects.update_or_create(slug=slug, defaults={"name": name, "group": group})[0] for name, slug, group in skill_names]
        password = "ProjectMate#2026"
        users = {}
        for username, first, last, email, staff in [("admin", "ProjectMate", "Admin", "admin@projectmate.local", True), ("demo", "Maya", "Singh", "maya@projectmate.local", False), ("owner_demo", "Jordan", "Lee", "jordan@projectmate.local", False), ("sam_student", "Sam", "Student", "sam@projectmate.local", False)]:
            user, created = User.objects.get_or_create(username=username, defaults={"first_name": first, "last_name": last, "email": email, "is_staff": staff, "is_superuser": staff})
            user.first_name, user.last_name, user.email, user.is_staff, user.is_superuser = first, last, email, staff, staff
            user.set_password(password)
            user.save()
            users[username] = user
        for skill in skill_objects[:6]:
            UserSkill.objects.get_or_create(user=users["demo"], skill=skill, defaults={"proficiency": 2})
        project_data = [
            ("Campus Pantry Planner", "Coordinate volunteer shifts and food inventory for students.", "course", "recruiting", category_objects[0]),
            ("Transit Delay Visualizer", "Explore bus reliability with a clear public dashboard.", "research", "recruiting", category_objects[2]),
            ("Accessible Study Timer", "Build a calm, keyboard-friendly focus timer.", "personal", "recruiting", category_objects[1]),
            ("Neighbourhood Safety Map", "Map community resources while protecting sensitive locations.", "competition", "full", category_objects[7]),
            ("Student Wellness Study", "Measure which campus supports students find easiest to access.", "research", "completed", category_objects[5]),
            ("Recipe Relay", "Share affordable recipes with a friendly mobile-first experience.", "hackathon", "recruiting", category_objects[6]),
            ("Robotics Lab Notebook", "Track experiments, observations, and equipment handoffs.", "course", "recruiting", category_objects[4]),
            ("Game Night Finder", "Help students discover welcoming campus game events.", "personal", "recruiting", category_objects[3]),
        ]
        projects = []
        for index, (title, summary, project_type, status, category) in enumerate(project_data, 1):
            project, _ = Project.objects.get_or_create(title=title, owner=users["owner_demo"], defaults={"summary": summary, "description": summary + " This realistic student project keeps scope clear and gives teammates a meaningful place to contribute.", "category": category, "project_type": project_type, "max_members": 2 if status == "full" else 4})
            project.status = status
            project.save()
            project.required_skills.set(skill_objects[(index - 1) % len(skill_objects):(index % len(skill_objects)) + 2])
            projects.append(project)
        full_project = projects[3]
        Membership.objects.get_or_create(project=full_project, user=users["demo"], defaults={"role": "member"})
        full_project.max_members = 2
        full_project.status = "full"
        full_project.save(update_fields=["max_members", "status"])
        JoinRequest.objects.get_or_create(project=projects[0], applicant=users["demo"], status="pending", defaults={"message": "I can contribute Python, testing, and clear documentation to this project."})
        JoinRequest.objects.get_or_create(project=projects[1], applicant=users["sam_student"], status="rejected", defaults={"message": "I would enjoy helping with the data story and dashboard."})
        resource, _ = ProjectResource.objects.get_or_create(project=projects[0], title="Project brief", uploaded_by=users["owner_demo"], defaults={"file": ContentFile(b"ProjectMate project brief\n", name="project-brief.txt"), "original_name": "project-brief.txt", "size_bytes": 25, "content_type": "text/plain", "is_public": True})
        self.stdout.write(self.style.SUCCESS("Demo data is ready."))
        self.stdout.write("Demo credentials: admin / demo / owner_demo / sam_student")
        self.stdout.write(f"Password: {password}")
