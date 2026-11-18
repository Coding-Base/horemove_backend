import os

from apps.accounts.models import User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Creates or updates a Super Administrator user safely from environment or flags."

    def add_arguments(self, parser):
        parser.add_argument("--email", type=str, help="Admin email address")
        parser.add_argument("--password", type=str, help="Admin password")

    def handle(self, *args, **options):
        email = options.get("email") or os.getenv("ADMIN_EMAIL", "admin@horemow.org")
        password = options.get("password") or os.getenv("ADMIN_PASSWORD", "HoremowAdmin2026!#")

        email = email.strip().lower()
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                "first_name": "Main",
                "last_name": "Administrator",
                "role": "SUPERADMIN",
                "capabilities": ["*"],
                "is_staff": True,
                "is_superuser": True,
            },
        )
        user.set_password(password)
        user.role = "SUPERADMIN"
        user.capabilities = ["*"]
        user.is_staff = True
        user.is_superuser = True
        user.save()

        action = "Created" if created else "Updated"
        self.stdout.write(self.style.SUCCESS(f"[OK] {action} Super Administrator: {email}"))
