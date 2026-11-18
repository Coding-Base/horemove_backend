import uuid

from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    ACTION_CHOICES = [
        ("CREATE", "Create Resource"),
        ("UPDATE", "Update Resource"),
        ("DELETE", "Delete Resource"),
        ("PUBLISH", "Publish Resource"),
        ("ARCHIVE", "Archive Resource"),
        ("EXPORT", "Export Records"),
        ("LOGIN_FAILED", "Failed Login"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_actions",
    )
    actor_email = models.EmailField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    action = models.CharField(max_length=32, choices=ACTION_CHOICES, db_index=True)
    resource_type = models.CharField(max_length=64, db_index=True)
    resource_id = models.CharField(max_length=64, blank=True)
    details = models.JSONField(default=dict, blank=True)
    request_id = models.CharField(max_length=64, blank=True, db_index=True)

    class Meta:
        verbose_name = "Audit Log Entry"
        verbose_name_plural = "Audit Log Entries"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"[{self.timestamp}] {self.actor_email or 'System'} - {self.action} on {self.resource_type}:{self.resource_id}"
