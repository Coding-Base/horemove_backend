from common.permissions import IsSuperAdminUser
from rest_framework import mixins, viewsets

from .models import AuditLog
from .serializers import AuditLogSerializer


class AuditLogViewSet(mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    Read-only audit log endpoint for security and compliance audits.
    Strictly limited to SuperAdmin.
    """

    queryset = AuditLog.objects.all().order_by("-timestamp")
    serializer_class = AuditLogSerializer
    permission_classes = [IsSuperAdminUser]
    filterset_fields = ["action", "resource_type", "actor_email"]
    search_fields = ["resource_id", "actor_email", "request_id"]
