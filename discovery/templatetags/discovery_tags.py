from django import template
from discovery.services import get_similar_projects

register = template.Library()


@register.inclusion_tag("discovery/similar_projects.html")
def similar_projects(project):
    return {
        "similar_projects": get_similar_projects(project)
    }
