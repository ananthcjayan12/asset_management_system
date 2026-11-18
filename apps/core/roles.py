from django.contrib.auth.models import Group, Permission

# Marking items outward/inward at the gate is reserved for the Security role, so
# the System Administrator group receives every permission except this one.
SECURITY_ONLY_PERMISSIONS = {"security_scan_gatepass"}

ROLE_DISPLAY_NAMES = {
    "System Administrator": "SPO (System Administrator)",
    "Stores Officer": "SO-Stores (Stores Officer)",
    "Asset Administrator": "DA (Dealing Assistant / Asset Admin)",
    "Division Administrator": "Dept HOD (Division Head)",
    "Approving Officer": "CA (Certifying Authority)",
    "Director": "Director",
    "Security Officer": "Security Officer",
    "Division Officer": "Staff / Employee",
}

GROUP_PERMISSIONS = {
    "System Administrator": ["add", "change", "delete", "view"],
    "Asset Administrator": [
        "da_complete_movement", "initiate_transfer", "initiate_return", "add_gatepass", "view_gatepass", "classify_lot",
        "add_asset", "change_asset", "view_asset", "add_procurement",
        "change_procurement", "view_procurement", "add_installation",
        "change_installation", "view_installation", "approve_assetmovement",
        "view_assetmovement", "add_disposalrecord", "change_disposalrecord",
        "view_disposalrecord", "add_importbatch", "change_importbatch",
        "view_importbatch", "add_assetverification", "view_assetverification",
    ],
    "Stores Officer": [
        "so_forward_movement",
        "view_asset", "change_asset", "approve_assetmovement",
        "view_assetmovement", "approve_gatepass", "view_gatepass",
        "change_gatepass", "add_disposalrecord", "change_disposalrecord",
        "view_disposalrecord", "classify_lot", "add_assetverification",
        "view_assetverification",
    ],
    "Division Administrator": [
        "initiate_transfer", "accept_transfer", "initiate_return", "hod_approve_movement", "view_disposalrecord",
        "view_asset", "add_gatepass", "view_gatepass", "division_approve_gatepass",
        "view_assetmovement", "view_assetverification",
    ],
    "Director": ["view_asset", "view_gatepass", "director_approve_gatepass", "view_assetmovement", "view_disposalrecord"],
    "Division Officer": [
        "view_asset", "add_gatepass", "view_gatepass", "view_assetmovement",
        "initiate_transfer", "accept_transfer", "initiate_return", "view_disposalrecord",
    ],
    "Approving Officer": [
        "ca_certify_return", "view_assetmovement",
        "view_asset", "approve_assetmovement", "approve_disposalrecord",
        "change_disposalrecord", "view_disposalrecord",
    ],
    "Security Officer": [
        "view_asset", "scan_asset", "view_gatepass",
        "security_scan_gatepass", "change_gatepass",
    ],
    "Auditor": [
        "view_asset", "view_procurement", "view_installation",
        "view_assetmovement", "view_gatepass", "view_disposalrecord",
        "view_auditevent", "view_assetverification",
    ],
    "Report Viewer": ["view_asset", "view_gatepass", "view_assetmovement", "view_disposalrecord", "view_assetverification"],
}


def ensure_groups() -> None:
    for name, codenames in GROUP_PERMISSIONS.items():
        group, _ = Group.objects.get_or_create(name=name)
        if name == "System Administrator":
            group.permissions.set(Permission.objects.exclude(codename__in=SECURITY_ONLY_PERMISSIONS))
        else:
            group.permissions.set(Permission.objects.filter(codename__in=codenames))
