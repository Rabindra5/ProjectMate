"""Project lifecycle helpers."""

def sync_project_status(project):
    """Keep recruiting/full status aligned with team capacity."""
    if project.status == "completed":
        return project
    project.status = "full" if project.memberships.count() >= project.max_members else "recruiting"
    project.save(update_fields=["status", "updated_at"])
    return project
