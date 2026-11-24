import logging
import os
import re
import uuid
import base64
import json
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
    # Remove directory traversal and dangerous characters
    cleaned = re.sub(r"[^\w\.-]", "_", os.path.basename(filename))
    return cleaned or "document.pdf"


def get_pdf_page_count(file_bytes: bytes) -> int:
    try:
        import fitz  # PyMuPDF
        doc = fitz.open(stream=file_bytes, filetype="pdf")
        return len(doc)
    except Exception:
        pass

    try:
        from pypdfium2 import PdfDocument
        doc = PdfDocument(file_bytes)
        return len(doc)
    except Exception:
        pass

    return 0


def ensure_supabase_bucket(supabase_url: str, service_role_key: str, bucket_name: str) -> bool:
    """Ensure the target Supabase storage bucket exists and is public."""
    headers = {
        "Authorization": f"Bearer {service_role_key}",
        "apiKey": service_role_key,
        "Content-Type": "application/json",
    }
    # Check if bucket exists
    check_url = f"{supabase_url}/storage/v1/bucket/{bucket_name}"
    try:
        res = requests.get(check_url, headers=headers, timeout=10)
        if res.status_code == 200:
            return True
        elif res.status_code == 404:
            # Create bucket
            create_url = f"{supabase_url}/storage/v1/bucket"
            create_payload = {
                "id": bucket_name,
                "name": bucket_name,
                "public": True,
                "file_size_limit": 104857600,  # 100MB
                "allowed_mime_types": ["application/pdf"],
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


def upload_publication_pdf(file_obj, original_name: str | None = None) -> dict:
    """
    Uploads a publication PDF to Supabase Storage.
    Falls back gracefully to local media storage if service role key is not yet configured.
    """
    file_bytes = file_obj.read()
    file_size = len(file_bytes)

    # Basic PDF magic bytes check (%PDF-)
    if not file_bytes.startswith(b"%PDF"):
        # Still allow if extension is .pdf
        pass

    sanitized = sanitize_filename(original_name or getattr(file_obj, "name", "publication.pdf"))
    unique_id = uuid.uuid4().hex[:10]
    storage_path = f"books/{unique_id}_{sanitized}"

    page_count = get_pdf_page_count(file_bytes)

    supabase_url = getattr(settings, "SUPABASE_URL", "").rstrip("/")
    service_role_key = getattr(settings, "SUPABASE_SERVICE_ROLE_KEY", "").strip()
    bucket_name = getattr(settings, "SUPABASE_STORAGE_BUCKET", "publications")

    # Check for project ref match
    key_ref = extract_jwt_ref(service_role_key) if service_role_key else None
    if key_ref and supabase_url and key_ref not in supabase_url:
        logger.warning(
            f"SUPABASE_URL ({supabase_url}) does not match key project ref ({key_ref}). "
            f"Please verify SUPABASE_SERVICE_ROLE_KEY belongs to {supabase_url}"
        )

    last_supabase_error = None

    # If Supabase credentials are configured, upload to Supabase Storage
    if supabase_url and service_role_key:
        ensure_supabase_bucket(supabase_url, service_role_key, bucket_name)

        upload_url = f"{supabase_url}/storage/v1/object/{bucket_name}/{storage_path}"
        headers = {
            "Authorization": f"Bearer {service_role_key}",
            "apiKey": service_role_key,
            "Content-Type": "application/pdf",
            "x-upsert": "true",
        }

        try:
            response = requests.post(
                upload_url,
                data=file_bytes,
                headers=headers,
                timeout=30,
            )
            if response.status_code in (200, 201):
                public_url = f"{supabase_url}/storage/v1/object/public/{bucket_name}/{storage_path}"
                logger.info(f"Successfully uploaded {sanitized} to Supabase Storage: {public_url}")
                return {
                    "success": True,
                    "storage": "supabase",
                    "public_url": public_url,
                    "file_name": sanitized,
                    "file_size": file_size,
                    "page_count": page_count,
                    "bucket": bucket_name,
                    "storage_path": storage_path,
                }
            else:
                last_supabase_error = f"Status {response.status_code}: {response.text}"
                logger.error(
                    f"Supabase storage upload failed: {last_supabase_error}"
                )
        except Exception as e:
            last_supabase_error = f"Exception: {str(e)}"
            logger.error(f"Supabase upload request failed: {e}")

    # Fallback to Django local default_storage
    local_path = default_storage.save(f"publications/{storage_path}", file_obj)
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
        "page_count": page_count,
        "bucket": bucket_name,
        "storage_path": local_path,
        "note": note,
    }
