"""
ASGI config for HOREMOW backend project.
"""

import os
from pathlib import Path

from django.core.asgi import get_asgi_application
from dotenv import load_dotenv

base_dir = Path(__file__).resolve().parent.parent
env_file = base_dir / ".env"
if env_file.exists():
    load_dotenv(env_file)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.development")

application = get_asgi_application()
