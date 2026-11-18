from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to allow anonymous users read-only access to published resources,
    requiring authentication for any state-changing operations.
    """

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class HasCapability(permissions.BasePermission):
    """
    Checks if an authenticated user possesses a specific domain capability.
    """

    def __init__(self, capability: str):
        self.capability = capability

    def __call__(self):
        return self

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_superuser:
            return True
        return request.user.has_capability(self.capability)


class IsSuperAdminUser(permissions.BasePermission):
    """
    Only accessible to superusers (Main Administrator).
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_superuser)


class IsFinanceAuditor(permissions.BasePermission):
    """
    Strict permission gating for financial transactions and donation reports.
    """

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
        if request.user.is_superuser:
            return True
        return request.user.role in ("SUPERADMIN", "FINANCE_AUDITOR")
