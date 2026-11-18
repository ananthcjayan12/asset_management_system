from django.contrib.auth.backends import ModelBackend


EMPLOYEE_PERMISSIONS = {
    "assets.view_asset",
    "gatepasses.add_gatepass",
    "gatepasses.view_gatepass",
    "movements.view_assetmovement",
    "movements.initiate_transfer",
    "movements.accept_transfer",
    "movements.initiate_return",
    "disposal.view_disposalrecord",
}


class EmployeePermissionsBackend(ModelBackend):
    def get_all_permissions(self, user_obj, obj=None):
        permissions = super().get_all_permissions(user_obj, obj)
        if obj is None and user_obj.is_active and getattr(user_obj, "employee", None):
            return permissions | EMPLOYEE_PERMISSIONS
        return permissions
