from apps.audit.utils import record_audit_log


class AuditedModelViewSetMixin:
    """
    Automatically creates append-only audit records for admin state-changing operations.
    """

    def perform_create(self, serializer):
        instance = serializer.save()
        record_audit_log(
            action="CREATE",
            resource_type=instance.__class__.__name__,
            resource_id=str(getattr(instance, "id", "")),
            request=self.request,
            details={"data": serializer.data},
        )
        return instance

    def perform_update(self, serializer):
        instance = serializer.save()
        record_audit_log(
            action="UPDATE",
            resource_type=instance.__class__.__name__,
            resource_id=str(getattr(instance, "id", "")),
            request=self.request,
            details={"data": serializer.data},
        )
        return instance

    def perform_destroy(self, instance):
        resource_id = str(getattr(instance, "id", ""))
        resource_type = instance.__class__.__name__
        instance.delete()
        record_audit_log(
            action="DELETE",
            resource_type=resource_type,
            resource_id=resource_id,
            request=self.request,
        )
