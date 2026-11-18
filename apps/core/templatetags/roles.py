from django import template

from apps.core.roles import ROLE_DISPLAY_NAMES

register = template.Library()


@register.simple_tag
def role_labels(user):
    names = [group.name for group in user.groups.all()]
    if user.is_superuser and "System Administrator" not in names:
        names.insert(0, "System Administrator")
    if not names and getattr(user, "employee", None):
        names.append("Division Officer")
    return ", ".join(ROLE_DISPLAY_NAMES.get(name, name) for name in names)
