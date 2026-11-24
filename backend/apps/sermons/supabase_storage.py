import logging
import os
import re
import uuid
import base64
import json
import mimetypes
import requests
from django.conf import settings
from django.core.files.storage import default_storage

logger = logging.getLogger(__name__)


def extract_jwt_ref(token: str) -> str | None:
    try:
        parts = token.split(".")
        if len(parts) >= 2:
            padded = parts[1] + "=" * (-len(parts[1]) % 4)
            data = json.loads(base64.b64decode(padded).decode("utf-8"))
            return data.get("ref")
    except Exception:
        pass
    return None


def sanitize_filename(filename: str) -> str:
    cleaned = re.sub(r"[^\w\.-]", "_", os.path.basename(filename))
    return cleaned or "sermon_audio.mp3"


def ensure_supabase_bucket(supabase_url: str, service_role_key: str, bucket_name: str) -> bool:
    """Ensure target Supabase storage bucket exists and is public."""
    headers = {
        "Authorization": f"Bearer {service_role_key}",
        "apiKey": service_role_key,
        "Content-Type": "application/json",
    }
    check_url = f"{supabase_url}/storage/v1/bucket/{bucket_name}"
    try:
        res = requests.get(check_url, headers=headers, timeout=10)
        if res.status_code == 200:
            return True
        elif res.status_code == 404:
            create_url = f"{supabase_url}/storage/v1/bucket"
            create_payload = {
                "id": bucket_name,
                "name": bucket_name,
                "public": True,
                "file_size_limit": 209715200,  # 200MB
            }
            create_res = requests.post(create_url, headers=headers, json=create_payload, timeout=10)
            if create_res.status_code in (200, 201):
                logger.info(f"Created public Supabase storage bucket '{bucket_name}'")
                return True
            else:
                logger.warning(f"Could not create Supabase bucket: {create_res.status_code} {create_res.text}")
    except Exception as e:
        logger.warning(f"Error checking/creating Supabase bucket '{bucket_name}': {e}")

    return False


def upload_sermon_audio(file_obj, original_name: str | None = None) -> dict:
    """
    Uploads a sermon audio file to Supabase Storage (bucket: 'sermons').
    Falls back gracefully to local media storage if service role key is not yet configured.
    """
    file_bytes = file_obj.read()
    file_size = len(file_bytes)

    sanitized = sanitize_filename(original_name or getattr(file_obj, "name", "audio.mp3"))
    unique_id = uuid.uuid4().hex[:10]
    storage_path = f"audio/{unique_id}_{sanitized}"

    # Determine content-type
    content_type, _ = mimetypes.guess_type(sanitized)
    if not content_type:
        content_type = getattr(file_obj, "content_type", "audio/mpeg") or "audio/mpeg"

    supabase_url = getattr(settings, "SUPABASE_URL", "").rstrip("/")
    service_role_key = getattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "").strip()
    bucket_name = getattr(settings, "SUPABASE_SERMONS_BUCKET", "sermons")

    # Check for project ref match
    key_ref = extract_jwt_ref(service_role_key) if service_role_key else None
    if key_ref and supabase_url and key_ref not in supabase_url:
        logger.warning(
            f"SUPABASE_URL ({supabase_url}) does not match key project ref ({key_ref}). "
            f"Please verify SUPABASE_SERVICE_ROLE_KEY belongs to {supabase_url}"
        )

    last_supabase_error = None

    if supabase_url and service_role_key:
        # Ensure bucket exists
        ensure_supabase_bucket(supabase_url, service_role_key, bucket_name)

        upload_url = f"{supabase_url}/storage/v1/object/{bucket_name}/{storage_path}"
        headers = {
            "Authorization": f"Bearer {service_role_key}",
            "apiKey": service_role_key,
            "Content-Type": content_type,
            "x-upsert": "true",
        }

        try:
            response = requests.post(
                upload_url,
                data=file_bytes,
                headers=headers,
                timeout=60,
            )
            if response.status_code in (200, 201):
                public_url = f"{supabase_url}/storage/v1/object/public/{bucket_name}/{storage_path}"
                logger.info(f"Successfully uploaded sermon audio {sanitized} to Supabase: {public_url}")
                return {
                    "success": True,
                    "storage": "supabase",
                    "public_url": public_url,
                    "file_name": sanitized,
                    "file_size": file_size,
                    "bucket": bucket_name,
                    "storage_path": storage_path,
                }
            else:
                last_supabase_error = f"Status {response.status_code}: {response.text}"
                logger.error(f"Supabase audio upload failed: {last_supabase_error}")
        except Exception as e:
            last_supabase_error = f"Exception: {str(e)}"
            logger.error(f"Supabase audio upload request failed: {e}")

    # Fallback to local default_storage
    local_path = default_storage.save(f"sermons/{storage_path}", file_obj)
    local_url = default_storage.url(local_path)

    note = "Uploaded to local storage fallback."
    if last_supabase_error:
        note += f" Supabase error: {last_supabase_error}"
    elif not service_role_key:
        note += " SUPABASE_SERVICE_ROLE_KEY is not configured."

    return {
        "success": True,
        "storage": "local_fallback",
        "public_url": local_url,
        "file_name": sanitized,
        "file_size": file_size,
        "bucket": bucket_name,
        "storage_path": local_path,
        "note": note,
    }
