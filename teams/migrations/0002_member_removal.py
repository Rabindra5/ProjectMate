import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("projects", "0001_initial"),
        ("teams", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AlterField(
            model_name="joinrequest",
            name="status",
            field=models.CharField(
                choices=[
                    ("pending", "Pending"),
                    ("accepted", "Accepted"),
                    ("rejected", "Rejected"),
                    ("withdrawn", "Withdrawn"),
                    ("cancelled", "Cancelled"),
                    ("removed", "Removed"),
                ],
                default="pending",
                max_length=12,
            ),
        ),
        migrations.CreateModel(
            name="MemberRemoval",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("reason", models.CharField(
                    choices=[
                        ("inactive", "Inactive or not contributing"),
                        ("missed_deadlines", "Repeatedly missed deadlines"),
                        ("conduct", "Conduct or collaboration issues"),
                        ("scope_change", "Project scope or team needs changed"),
                        ("member_request", "Member asked to be removed"),
                        ("other", "Other"),
                    ],
                    max_length=30,
                )),
                ("details", models.CharField(max_length=300)),
                ("removed_at", models.DateTimeField(auto_now_add=True)),
                ("project", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="member_removals", to="projects.project")),
                ("removed_by", models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="performed_removals", to=settings.AUTH_USER_MODEL)),
                ("user", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="project_removals", to=settings.AUTH_USER_MODEL)),
            ],
            options={"ordering": ["-removed_at"]},
        ),
    ]