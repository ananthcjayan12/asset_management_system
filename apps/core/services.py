from .models import AuditEvent

def audit(*, actor, action, obj, description, metadata=None):
    return AuditEvent.objects.create(
        actor=actor if getattr(actor, "is_authenticated", False) else None,
        action=action,
        object_type=obj.__class__.__name__,
        object_id=str(getattr(obj, "pk", "")),
        description=description,
        metadata=metadata or {},
    )
