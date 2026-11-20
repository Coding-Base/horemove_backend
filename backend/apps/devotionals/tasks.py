import datetime
import logging
from typing import Any
from zoneinfo import ZoneInfo

from django.conf import settings
from django.db import transaction
from django.utils import timezone
from django.utils.text import slugify

from .models import AutoPublishSettings, Devotional, DevotionalBatch, DevotionalParsedEntry
from .parser import parse_devotional_pdf

logger = logging.getLogger(__name__)


def run_batch_parsing(batch_id: str) -> None:
    """
    Executes PDF parsing on a batch. Can be invoked directly or queued.
    """
    try:
        batch = DevotionalBatch.objects.get(id=batch_id)
    except DevotionalBatch.DoesNotExist:
        logger.error(f"DevotionalBatch {batch_id} not found.")
        return

    batch.status = "PARSING"
    batch.error_log = ""
    batch.save(update_fields=["status", "error_log"])

    try:
        if not batch.file:
            raise ValueError("No file attached to batch.")

        file_path = batch.file.path
        default_author = "Pastor Paul Rika"
        if batch.uploaded_by:
            full = f"{batch.uploaded_by.first_name} {batch.uploaded_by.last_name}".strip()
            if full:
                default_author = full

        # Retrieve configured AI OCR model and API key from database or settings
        auto_settings = AutoPublishSettings.objects.first()
        ocr_model = "gemini-3.1-flash-lite-preview"
        ocr_api_key = ""
        if auto_settings:
            ocr_model = auto_settings.ocr_model or "gemini-3.1-flash-lite-preview"
            ocr_api_key = (auto_settings.ocr_api_key or auto_settings.gemini_api_key or "").strip()
        if not ocr_api_key:
            ocr_api_key = getattr(settings, "GEMINI_API_KEY", "")

        # Clear any previous parsed entries for this batch
        batch.entries.all().delete()

        def on_page_progress(processed: int, total: int, entry_dict: Any):
            batch.processed_pages = processed
            batch.total_pages = total
            if entry_dict:
                # Save entry incrementally so admin sees live streaming progress
                entry_date = entry_dict.get("date")
                if entry_date:
                    DevotionalParsedEntry.objects.update_or_create(
                        batch=batch,
                        date=entry_date,
                        defaults={
                            "title": entry_dict.get("title") or "Daily Devotional",
                            "text_reference": entry_dict.get("text_reference") or "",
                            "text_body": entry_dict.get("text_body") or "",
                            "key_verse_reference": entry_dict.get("key_verse_reference") or "",
                            "key_verse_text": entry_dict.get("key_verse_text") or "",
                            "reflection_body": entry_dict.get("reflection_body") or "",
                            "thought_for_day": entry_dict.get("thought_for_day") or "",
                            "song_for_day": entry_dict.get("song_for_day") or "",
                            "bible_reading_for_day": entry_dict.get("bible_reading_for_day") or "",
                            "author_attribution": entry_dict.get("author_attribution") or default_author,
                            "prayer_points": entry_dict.get("prayer_points") or [],
                            "action_point": entry_dict.get("action_point") or "",
                            "has_parsing_issues": entry_dict.get("has_parsing_issues", False),
                            "parsing_notes": entry_dict.get("parsing_notes") or "",
                            "order": entry_dict.get("order", 0),
                        },
                    )
            batch.parsed_entries = batch.entries.count()
            batch.save(update_fields=["processed_pages", "total_pages", "parsed_entries"])

        parsed_data = parse_devotional_pdf(
            file_path,
            default_author=default_author,
            target_year=batch.target_year or 2026,
            start_page=batch.start_page or 1,
            end_page=batch.end_page or 184,
            ocr_model=ocr_model,
            api_key=ocr_api_key,
            progress_callback=on_page_progress,
        )

        if not parsed_data and batch.entries.count() == 0:
            raise ValueError("No valid devotional entries could be extracted from the uploaded PDF.")

        # If not streamed via callback (e.g. digital text fast parser), create entries in bulk:
        if batch.entries.count() == 0:
            with transaction.atomic():
                valid_dates = []
                entries_to_create = []

                for item in parsed_data:
                    entry_date = item.get("date")
                    if not entry_date:
                        entry_date = timezone.localdate() + datetime.timedelta(days=len(valid_dates))
                        item["has_parsing_issues"] = True
                        item["parsing_notes"] = (item.get("parsing_notes", "") + "; Assigned fallback date").lstrip("; ")

                    valid_dates.append(entry_date)

                    entries_to_create.append(
                        DevotionalParsedEntry(
                            batch=batch,
                            date=entry_date,
                            title=item.get("title") or "Daily Devotional",
                            text_reference=item.get("text_reference") or "",
                            text_body=item.get("text_body") or "",
                            key_verse_reference=item.get("key_verse_reference") or "",
                            key_verse_text=item.get("key_verse_text") or "",
                            reflection_body=item.get("reflection_body") or "",
                            thought_for_day=item.get("thought_for_day") or "",
                            song_for_day=item.get("song_for_day") or "",
                            bible_reading_for_day=item.get("bible_reading_for_day") or "",
                            author_attribution=item.get("author_attribution") or default_author,
                            prayer_points=item.get("prayer_points") or [],
                            action_point=item.get("action_point") or "",
                            has_parsing_issues=item.get("has_parsing_issues", False),
                            parsing_notes=item.get("parsing_notes") or "",
                            order=item.get("order", 0),
                        )
                    )

                DevotionalParsedEntry.objects.bulk_create(entries_to_create)

        all_dates = list(batch.entries.values_list("date", flat=True))
        batch.total_entries = len(all_dates)
        batch.parsed_entries = len(all_dates)
        if all_dates:
            batch.date_range_start = min(all_dates)
            batch.date_range_end = max(all_dates)
        batch.status = "REVIEW"
        batch.save()

        logger.info(f"Successfully processed {len(all_dates)} devotionals for batch {batch.id}")

    except Exception as e:
        logger.exception(f"Error parsing devotional batch {batch_id}: {e}")
        batch.status = "FAILED"
        batch.error_log = str(e)
        batch.save(update_fields=["status", "error_log"])


def confirm_and_import_batch(batch_id: str, replace_conflicts: bool = True) -> int:
    """
    Imports parsed entries into the live Devotional database table.
    """
    batch = DevotionalBatch.objects.get(id=batch_id)
    parsed_entries = batch.entries.all().order_by("date")

    if not parsed_entries.exists():
        raise ValueError("Batch has no parsed entries to import.")

    imported_count = 0

    with transaction.atomic():
        for item in parsed_entries:
            if replace_conflicts:
                Devotional.objects.filter(date=item.date).delete()
            else:
                if Devotional.objects.filter(date=item.date).exists():
                    continue

            base_slug = slugify(item.title)
            slug = f"{item.date}-{base_slug}"[:280]

            Devotional.objects.create(
                date=item.date,
                title=item.title,
                slug=slug,
                text_reference=item.text_reference,
                text_body=item.text_body,
                key_verse_reference=item.key_verse_reference,
                key_verse_text=item.key_verse_text,
                scripture_reading=item.text_reference,
                memory_verse_reference=item.key_verse_reference,
                memory_verse_text=item.key_verse_text,
                reflection_body=item.reflection_body,
                thought_for_day=item.thought_for_day,
                song_for_day=item.song_for_day,
                bible_reading_for_day=item.bible_reading_for_day,
                author_attribution=item.author_attribution,
                prayer_points=item.prayer_points,
                action_point=item.action_point,
                status="DRAFT",
                batch=batch,
            )
            imported_count += 1

        batch.status = "CONFIRMED"
        batch.save(update_fields=["status"])

    # Trigger immediate auto-publish check in case today's entry was imported and is due
    check_and_auto_publish_devotionals()
    return imported_count


def check_and_auto_publish_devotionals() -> int:
    """
    Checks if today's or earlier DRAFT devotionals are due for publication based on AutoPublishSettings.
    """
    settings_obj = AutoPublishSettings.load()
    if not settings_obj.is_enabled:
        return 0

    try:
        tz = ZoneInfo(settings_obj.timezone_name)
    except Exception:
        tz = ZoneInfo("Africa/Lagos")

    now = timezone.now().astimezone(tz)
    current_date = now.date()
    current_time = now.time()

    published_count = 0

    # Auto-publish candidates:
    # 1. Past dates that were DRAFT (should always be published)
    # 2. Today's devotional, IF current time >= publish_time
    past_due_devotionals = Devotional.objects.filter(
        status="DRAFT",
        date__lt=current_date,
    )

    for dev in past_due_devotionals:
        dev.status = "PUBLISHED"
        dev.published_at = timezone.now()
        dev.save(update_fields=["status", "published_at"])
        published_count += 1

    if current_time >= settings_obj.publish_time:
        today_devotionals = Devotional.objects.filter(
            status="DRAFT",
            date=current_date,
        )
        for dev in today_devotionals:
            dev.status = "PUBLISHED"
            dev.published_at = timezone.now()
            dev.save(update_fields=["status", "published_at"])
            published_count += 1

    if published_count > 0:
        logger.info(f"Auto-published {published_count} devotional(s).")

    return published_count
