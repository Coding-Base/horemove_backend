import json
import os
from decimal import Decimal
from django.conf import settings
from django.core.management.base import BaseCommand
from apps.locations.models import Fellowship, Region

# Try project root or django base dir
POSSIBLE_PATHS = [
    os.path.join(settings.BASE_DIR, "apps", "locations", "data", "defaultLocations.json"),
    os.path.join(settings.BASE_DIR.parent, "frontend", "src", "lib", "defaultLocations.json"),
    os.path.join(os.getcwd(), "frontend", "src", "lib", "defaultLocations.json"),
]


class Command(BaseCommand):
    help = "Seeds HOREMOW fellowship locations and regions worldwide from the telephone directory."

    def handle(self, *args, **options):
        json_path = None
        for p in POSSIBLE_PATHS:
            if os.path.exists(p):
                json_path = p
                break

        if not json_path:
            self.stderr.write(self.style.ERROR(f"Data file defaultLocations.json not found in paths: {POSSIBLE_PATHS}"))
            return

        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        created_regions = 0
        created_fellowships = 0
        updated_fellowships = 0

        for item in data:
            region, r_created = Region.objects.get_or_create(
                continent=item["continent"],
                country=item["country"],
                state_or_province=item["stateOrArea"],
            )
            if r_created:
                created_regions += 1

            contact_name = item.get("overseerName") or item.get("name")
            contact_title = item.get("overseerTitle") or "Coordinator"
            contact_display = f"{contact_name} ({contact_title})" if contact_title else contact_name

            fellowship, f_created = Fellowship.objects.update_or_create(
                name=item["name"],
                region=region,
                defaults={
                    "city_or_lga": item["stateOrArea"],
                    "address": item["address"],
                    "meeting_schedule": "Sunday Worship Service (8:30 AM) & Tuesday Bible Study / Thursday Revival (5:30 PM)",
                    "contact_person": contact_display,
                    "contact_phone": item.get("overseerPhone") or item.get("phone", ""),
                    "contact_email": item.get("overseerEmail") or item.get("email", ""),
                    "latitude": Decimal(str(item["latitude"])) if item.get("latitude") is not None else None,
                    "longitude": Decimal(str(item["longitude"])) if item.get("longitude") is not None else None,
                    "is_active": True,
                },
            )

            if f_created:
                created_fellowships += 1
            else:
                updated_fellowships += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully seeded {created_fellowships} new fellowships ({updated_fellowships} updated) across {created_regions} new regions."
            )
        )
