from django.db.models import Q

ASSET_REGISTER_ROLES = {
    "System Administrator", "Stores Officer", "Asset Administrator", "Auditor", "Report Viewer", "Security Officer",
}


def employee_assets(queryset, employee, *, include_division=False):
    if employee is None:
        return queryset.none()
    scope = Q(current_custodian=employee)
    if include_division and employee.division_id:
        scope |= Q(division_id=employee.division_id)
    return queryset.filter(scope)


def visible_assets(queryset, user):
    employee = getattr(user, "employee", None)
    if employee and not (user.is_superuser or user.groups.filter(name__in=ASSET_REGISTER_ROLES).exists()):
        return employee_assets(queryset, employee, include_division=True)
    return queryset
